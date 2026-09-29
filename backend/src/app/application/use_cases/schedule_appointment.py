"""Caso de uso: agendar una cita nueva."""

from __future__ import annotations

import logging

from app.application.dto.appointment_dto import (
    AppointmentResult,
    ScheduleAppointmentCommand,
)
from app.application.services import notification_messages
from app.domain.entities.appointment import Appointment
from app.domain.entities.person import Doctor, Patient
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


class ScheduleAppointmentUseCase:
    """Agenda una cita y notifica al paciente.

    Orquesta el flujo completo: valida que paciente y doctor existan, construye
    la franja horaria, verifica que no choque con la agenda del doctor,
    persiste, y -solo si todo lo anterior funciono- intenta notificar.
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
        """Recibe sus colaboradores por inyeccion de dependencias.

        Args:
            appointments: Repositorio de citas.
            patients: Repositorio de pacientes.
            doctors: Repositorio de doctores.
            notifier: Canal de notificacion saliente.
            clock: Fuente de la hora actual.
        """
        self._appointments = appointments
        self._patients = patients
        self._doctors = doctors
        self._notifier = notifier
        self._clock = clock

    def execute(self, command: ScheduleAppointmentCommand) -> AppointmentResult:
        """Agenda la cita descrita por el comando.

        Args:
            command: Datos de la cita a crear.

        Returns:
            La cita persistida junto con los nombres de paciente y doctor, y si
            la notificacion pudo entregarse.

        Raises:
            NotFoundException: Si el paciente o el doctor no existen.
            InvalidInputException: Si la franja esta en el pasado o el motivo
                no cumple la longitud minima.
            ConflictException: Si el doctor ya tiene una cita en ese horario.
        """
        patient = self._patients.get(command.patient_id)
        if patient is None:
            raise NotFoundException("Paciente", command.patient_id)

        doctor = self._doctors.get(command.doctor_id)
        if doctor is None:
            raise NotFoundException("Doctor", command.doctor_id)

        slot = TimeSlot(
            date=command.date,
            start_time=command.start_time,
            duration_minutes=command.duration_minutes,
        )
        appointment = Appointment.schedule(
            patient_id=command.patient_id,
            doctor_id=command.doctor_id,
            slot=slot,
            reason=command.reason,
            now=self._clock.now(),
        )

        self._ensure_doctor_is_available(appointment)
        saved = self._appointments.add(appointment)

        sent = self._notify(saved, patient, doctor)
        return AppointmentResult(
            appointment=saved,
            patient_name=patient.full_name,
            doctor_name=doctor.display_name,
            notification_sent=sent,
        )

    def _ensure_doctor_is_available(self, appointment: Appointment) -> None:
        """Verifica que la franja no choque con la agenda del doctor.

        Raises:
            ConflictException: Si existe al menos un traslape.
        """
        agenda = self._appointments.list_for_doctor_on(appointment.doctor_id, appointment.slot.date)
        if any(appointment.conflicts_with(existing) for existing in agenda):
            raise ConflictException("El doctor ya tiene una cita en ese horario.")

    def _notify(self, appointment: Appointment, patient: Patient, doctor: Doctor) -> bool:
        """Intenta avisar al paciente sin comprometer la operacion principal.

        La cita ya quedo guardada; si el proveedor de mensajeria falla se
        registra el incidente y se informa al usuario, pero no se revierte.
        """
        if patient.phone is None:
            logger.info(
                "Paciente %s sin telefono registrado; se omite la notificacion.", patient.id
            )
            return False
        message = notification_messages.appointment_scheduled(appointment, doctor)
        return self._notifier.send(patient.phone, message)
