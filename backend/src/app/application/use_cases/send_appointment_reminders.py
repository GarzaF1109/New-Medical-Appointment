"""Caso de uso: enviar recordatorios de las citas de manana."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import timedelta

from app.application.services import notification_messages
from app.domain.entities.appointment import AppointmentStatus
from app.domain.ports.clock import Clock
from app.domain.ports.notifications import NotificationSender
from app.domain.ports.repositories import (
    AppointmentRepository,
    DoctorRepository,
    PatientRepository,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ReminderReport:
    """Resumen de una corrida de recordatorios.

    Attributes:
        total: Citas encontradas para el dia objetivo.
        sent: Recordatorios entregados.
        skipped: Pacientes sin telefono registrado.
        failed: Envios rechazados por el proveedor.
    """

    total: int
    sent: int
    skipped: int
    failed: int


class SendAppointmentRemindersUseCase:
    """Notifica a los pacientes con cita dentro de 24 horas.

    Equivale al comando `appointments:send-reminders` de Laravel, pero como
    caso de uso puede invocarse tanto desde un cron como desde un endpoint
    administrativo, y probarse sin arrancar la aplicacion.
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

    def execute(self) -> ReminderReport:
        """Recorre las citas de manana y envia un recordatorio por cada una.

        Returns:
            Un resumen con los conteos de la corrida.
        """
        tomorrow = (self._clock.now() + timedelta(days=1)).date()
        pending, _ = self._appointments.list(
            status=AppointmentStatus.PENDING,
            date_from=tomorrow,
            date_to=tomorrow,
            limit=1000,
        )

        sent = skipped = failed = 0
        for appointment in pending:
            patient = self._patients.get(appointment.patient_id)
            doctor = self._doctors.get(appointment.doctor_id)
            if patient is None or doctor is None or not patient.is_reachable:
                skipped += 1
                logger.info("Cita %s omitida: paciente sin telefono.", appointment.id)
                continue

            message = notification_messages.appointment_reminder(appointment, doctor)
            if self._notifier.send(patient.phone, message):
                sent += 1
            else:
                failed += 1
                logger.warning("Fallo el recordatorio de la cita %s.", appointment.id)

        return ReminderReport(total=len(pending), sent=sent, skipped=skipped, failed=failed)
