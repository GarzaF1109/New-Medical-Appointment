"""Caso de uso: reagendar o reasignar una cita existente."""

from __future__ import annotations

import logging
from datetime import timedelta

from app.application.dto.appointment_dto import (
    AppointmentResult,
    RescheduleAppointmentCommand,
)
from app.application.services import notification_messages
from app.domain.entities.appointment import Appointment
from app.domain.exceptions import ConflictException, NotFoundException
from app.domain.ports.clock import Clock
from app.domain.ports.notifications import NotificationSender
from app.domain.ports.repositories import (
    AppointmentRepository,
    DoctorRepository,
    PatientRepository,
)
from app.domain.value_objects.time_slot import TimeSlot

logger = logging.getLogger(__name__)


class RescheduleAppointmentUseCase:
    """Actualiza una cita y notifica solo cuando el cambio afecta al paciente.

    Reemplaza a `AppointmentEdit::updateAppointment()` y a
    `AppointmentController::moveTo24Hours()`, que compartian esta logica
    duplicada. Un cambio unicamente en el motivo no dispara notificacion.
    """

    def __init__(
        self,
        *,
        appointments: AppointmentRepository,
        patients: PatientRepository,
        doctors: DoctorRepository,
        notifier: NotificationSender,
        clock: Clock,
    ) -> None:
        self._appointments = appointments
        self._patients = patients
        self._doctors = doctors
        self._notifier = notifier
        self._clock = clock

    def execute(self, command: RescheduleAppointmentCommand) -> AppointmentResult:
        """Aplica los cambios solicitados sobre la cita.

        Args:
            command: Identificador de la cita y campos a modificar. Los campos
                en None se dejan intactos.

        Returns:
            La cita actualizada y si se notifico al paciente.

        Raises:
            NotFoundException: Si la cita, el paciente o el doctor no existen.
            ConflictException: Si la cita esta en estado terminal o el nuevo
                horario choca con la agenda del doctor.
            InvalidInputException: Si el nuevo horario esta en el pasado.
        """
        appointment = self._appointments.get(command.appointment_id)
        if appointment is None:
            raise NotFoundException("Cita", command.appointment_id)

        previous_patient_id = appointment.patient_id
        schedule_changed = self._apply_schedule(appointment, command)
        assignment_changed = self._apply_assignment(appointment, command)

        if command.reason is not None:
            appointment.change_reason(command.reason)

        if schedule_changed or assignment_changed:
            self._ensure_doctor_is_available(appointment)

        updated = self._appointments.update(appointment)

        patient = self._require_patient(updated.patient_id)
        doctor = self._require_doctor(updated.doctor_id)

        sent = self._notify(
            updated,
            patient,
            doctor,
            previous_patient_id=previous_patient_id,
            notify=schedule_changed or assignment_changed,
        )
        return AppointmentResult(
            appointment=updated,
            patient_name=patient.full_name,
            doctor_name=doctor.display_name,
            notification_sent=sent,
        )

    def move_to_next_day(self, appointment_id: int) -> AppointmentResult:
        """Mueve una cita al dia siguiente conservando su hora.

        Sustituye al endpoint `POST /appointments/{id}/move-to-24hours`, que
        ademas de duplicar logica no revalidaba conflictos de horario.
        """
        appointment = self._appointments.get(appointment_id)
        if appointment is None:
            raise NotFoundException("Cita", appointment_id)
        return self.execute(
            RescheduleAppointmentCommand(
                appointment_id=appointment_id,
                date=appointment.slot.date + timedelta(days=1),
            )
        )

    def _apply_schedule(
        self, appointment: Appointment, command: RescheduleAppointmentCommand
    ) -> bool:
        """Reagenda la cita si el comando trae algun dato de horario.

        Returns:
            True si la franja horaria efectivamente cambio.
        """
        if command.date is None and command.start_time is None and command.duration_minutes is None:
            return False

        new_slot = TimeSlot(
            date=command.date or appointment.slot.date,
            start_time=command.start_time or appointment.slot.start_time,
            duration_minutes=command.duration_minutes or appointment.slot.duration_minutes,
        )
        if new_slot == appointment.slot:
            return False

        appointment.reschedule(new_slot, self._clock.now())
        return True

    def _apply_assignment(
        self, appointment: Appointment, command: RescheduleAppointmentCommand
    ) -> bool:
        """Reasigna paciente o doctor si el comando lo pide.

        Returns:
            True si alguno de los dos cambio.
        """
        new_patient_id = command.patient_id or appointment.patient_id
        new_doctor_id = command.doctor_id or appointment.doctor_id
        if (new_patient_id, new_doctor_id) == (appointment.patient_id, appointment.doctor_id):
            return False

        if command.patient_id is not None and self._patients.get(command.patient_id) is None:
            raise NotFoundException("Paciente", command.patient_id)
        if command.doctor_id is not None and self._doctors.get(command.doctor_id) is None:
            raise NotFoundException("Doctor", command.doctor_id)

        appointment.reassign(patient_id=new_patient_id, doctor_id=new_doctor_id)
        return True

    def _ensure_doctor_is_available(self, appointment: Appointment) -> None:
        agenda = self._appointments.list_for_doctor_on(appointment.doctor_id, appointment.slot.date)
        if any(appointment.conflicts_with(existing) for existing in agenda):
            raise ConflictException("El doctor ya tiene una cita en ese horario.")

    def _require_patient(self, patient_id: int):
        patient = self._patients.get(patient_id)
        if patient is None:
            raise NotFoundException("Paciente", patient_id)
        return patient

    def _require_doctor(self, doctor_id: int):
        doctor = self._doctors.get(doctor_id)
        if doctor is None:
            raise NotFoundException("Doctor", doctor_id)
        return doctor

    def _notify(
        self,
        appointment: Appointment,
        patient,
        doctor,
        *,
        previous_patient_id: int,
        notify: bool,
    ) -> bool | None:
        """Avisa a los pacientes afectados por el cambio.

        Si la cita se transfirio a otro paciente, el anterior recibe un aviso de
        cancelacion antes de que el nuevo reciba la confirmacion.

        Returns:
            True o False segun el envio al paciente actual; None si el cambio no
            ameritaba notificacion.
        """
        if not notify:
            return None

        if previous_patient_id != appointment.patient_id:
            self._notify_previous_patient(previous_patient_id, appointment)

        if not patient.is_reachable:
            logger.info(
                "Paciente %s sin telefono registrado; se omite la notificacion.", patient.id
            )
            return False

        message = notification_messages.appointment_rescheduled(appointment, doctor)
        return self._notifier.send(patient.phone, message)

    def _notify_previous_patient(self, patient_id: int, appointment: Appointment) -> None:
        previous = self._patients.get(patient_id)
        if previous is None or not previous.is_reachable:
            return
        self._notifier.send(
            previous.phone, notification_messages.appointment_cancelled(appointment)
        )
