"""Casos de uso de transicion de estado de una cita."""

from __future__ import annotations

import logging

from app.application.dto.appointment_dto import AppointmentResult
from app.application.services import notification_messages
from app.domain.entities.appointment import Appointment
from app.domain.exceptions import NotFoundException
from app.domain.ports.notifications import NotificationSender
from app.domain.ports.repositories import (
    AppointmentRepository,
    DoctorRepository,
    PatientRepository,
)

logger = logging.getLogger(__name__)


class ChangeAppointmentStatusUseCase:
    """Confirma, completa o cancela una cita.

    Las tres operaciones comparten el mismo esqueleto -cargar, transicionar,
    guardar- por lo que viven juntas; la regla de que transiciones son legales
    pertenece a la entidad, no a este caso de uso.
    """

    def __init__(
        self,
        *,
        appointments: AppointmentRepository,
        patients: PatientRepository,
        doctors: DoctorRepository,
        notifier: NotificationSender,
    ) -> None:
        self._appointments = appointments
        self._patients = patients
        self._doctors = doctors
        self._notifier = notifier

    def confirm(self, appointment_id: int) -> AppointmentResult:
        """Marca la cita como confirmada por el paciente."""
        return self._transition(appointment_id, lambda a: a.confirm(), notify=False)

    def complete(self, appointment_id: int) -> AppointmentResult:
        """Marca la cita como atendida."""
        return self._transition(appointment_id, lambda a: a.complete(), notify=False)

    def cancel(self, appointment_id: int) -> AppointmentResult:
        """Cancela la cita y avisa al paciente."""
        return self._transition(appointment_id, lambda a: a.cancel(), notify=True)

    def _transition(self, appointment_id: int, action, *, notify: bool) -> AppointmentResult:
        """Aplica una transicion de estado y persiste el resultado.

        Args:
            appointment_id: Cita a modificar.
            action: Metodo de la entidad que ejecuta la transicion.
            notify: Si debe avisarse al paciente del cambio.

        Raises:
            NotFoundException: Si la cita no existe.
            ConflictException: Si la transicion no es legal desde el estado
                actual; la lanza la propia entidad.
        """
        appointment = self._appointments.get(appointment_id)
        if appointment is None:
            raise NotFoundException("Cita", appointment_id)

        action(appointment)
        updated = self._appointments.update(appointment)

        patient = self._patients.get(updated.patient_id)
        doctor = self._doctors.get(updated.doctor_id)
        sent = self._notify(updated, patient) if notify else None

        return AppointmentResult(
            appointment=updated,
            patient_name=patient.full_name if patient else "Desconocido",
            doctor_name=doctor.display_name if doctor else "Desconocido",
            notification_sent=sent,
        )

    def _notify(self, appointment: Appointment, patient) -> bool:
        if patient is None or not patient.is_reachable:
            return False
        return self._notifier.send(
            patient.phone, notification_messages.appointment_cancelled(appointment)
        )
