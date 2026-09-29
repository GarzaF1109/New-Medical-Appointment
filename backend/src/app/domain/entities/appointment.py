"""Entidad de dominio: Cita medica."""

from __future__ import annotations

from datetime import datetime
from enum import IntEnum

from app.domain.exceptions import ConflictException, InvalidInputException
from app.domain.text_rules import validate_free_text
from app.domain.value_objects.time_slot import TimeSlot

MIN_REASON_LENGTH = 10
MAX_REASON_LENGTH = 500


class AppointmentStatus(IntEnum):
    """Estados posibles de una cita.

    Los valores numericos se conservan del sistema Laravel para que la
    migracion de datos sea directa.
    """

    PENDING = 1
    CONFIRMED = 2
    COMPLETED = 3
    CANCELLED = 4

    @property
    def label(self) -> str:
        """Etiqueta legible en espanol."""
        return {
            AppointmentStatus.PENDING: "Pendiente",
            AppointmentStatus.CONFIRMED: "Confirmada",
            AppointmentStatus.COMPLETED: "Completada",
            AppointmentStatus.CANCELLED: "Cancelada",
        }[self]

    @property
    def is_final(self) -> bool:
        """Indica si el estado es terminal y ya no admite transiciones."""
        return self in (AppointmentStatus.COMPLETED, AppointmentStatus.CANCELLED)


class Appointment:
    """Cita entre un paciente y un doctor.

    Esta clase no sabe nada de SQL, HTTP ni WhatsApp: es una entidad pura. Las
    transiciones de estado son metodos que protegen las invariantes, en lugar de
    asignaciones sueltas a un campo `status` desde un controlador.
    """

    def __init__(
        self,
        *,
        patient_id: int,
        doctor_id: int,
        slot: TimeSlot,
        reason: str,
        status: AppointmentStatus = AppointmentStatus.PENDING,
        id: int | None = None,
    ) -> None:
        """Inicializa una cita.

        Args:
            patient_id: Identificador del paciente.
            doctor_id: Identificador del doctor.
            slot: Franja horaria reservada.
            reason: Motivo de la consulta.
            status: Estado inicial. Por defecto, pendiente.
            id: Identificador persistido. None si aun no se ha guardado.

        Raises:
            InvalidInputException: Si el motivo no cumple la longitud requerida.
        """
        self.id = id
        self.patient_id = patient_id
        self.doctor_id = doctor_id
        self.slot = slot
        self.reason = self._validate_reason(reason)
        self.status = status

    @staticmethod
    def _validate_reason(reason: str) -> str:
        return validate_free_text(
            reason,
            field="El motivo de la consulta",
            min_len=MIN_REASON_LENGTH,
            max_len=MAX_REASON_LENGTH,
        )

    @classmethod
    def schedule(
        cls,
        *,
        patient_id: int,
        doctor_id: int,
        slot: TimeSlot,
        reason: str,
        now: datetime,
    ) -> Appointment:
        """Agenda una cita nueva.

        Args:
            patient_id: Identificador del paciente.
            doctor_id: Identificador del doctor.
            slot: Franja horaria solicitada.
            reason: Motivo de la consulta.
            now: Instante actual, inyectado para pruebas deterministas.

        Returns:
            Una cita en estado pendiente.

        Raises:
            InvalidInputException: Si la franja ya paso o el motivo es invalido.
        """
        if slot.is_in_the_past(now):
            raise InvalidInputException("No se puede agendar una cita en el pasado.")
        if slot.is_too_far_ahead(now):
            raise InvalidInputException(
                "No se puede agendar una cita con mas de dos anos de anticipacion."
            )
        return cls(patient_id=patient_id, doctor_id=doctor_id, slot=slot, reason=reason)

    def conflicts_with(self, other: Appointment) -> bool:
        """Indica si esta cita choca con otra del mismo doctor.

        Una cita cancelada libera su horario, de modo que nunca genera conflicto.

        Args:
            other: Cita candidata a colisionar.

        Returns:
            True si ambas ocupan al mismo doctor en horarios traslapados.
        """
        if self.id is not None and self.id == other.id:
            return False
        if self.doctor_id != other.doctor_id:
            return False
        if AppointmentStatus.CANCELLED in (self.status, other.status):
            return False
        return self.slot.overlaps(other.slot)

    def reschedule(self, new_slot: TimeSlot, now: datetime) -> None:
        """Mueve la cita a una nueva franja horaria.

        Args:
            new_slot: Franja destino.
            now: Instante actual.

        Raises:
            ConflictException: Si la cita ya esta completada o cancelada.
            InvalidInputException: Si la franja destino ya paso.
        """
        if self.status.is_final:
            raise ConflictException(f"No se puede reagendar una cita {self.status.label.lower()}.")
        if new_slot.is_in_the_past(now):
            raise InvalidInputException("No se puede reagendar una cita al pasado.")
        if new_slot.is_too_far_ahead(now):
            raise InvalidInputException(
                "No se puede reagendar una cita con mas de dos anos de anticipacion."
            )
        self.slot = new_slot

    def reassign(self, *, patient_id: int, doctor_id: int) -> None:
        """Cambia el paciente o el doctor asignado.

        Raises:
            ConflictException: Si la cita ya alcanzo un estado terminal.
        """
        if self.status.is_final:
            raise ConflictException(f"No se puede reasignar una cita {self.status.label.lower()}.")
        self.patient_id = patient_id
        self.doctor_id = doctor_id

    def change_reason(self, reason: str) -> None:
        """Actualiza el motivo de la consulta."""
        self.reason = self._validate_reason(reason)

    def confirm(self) -> None:
        """Marca la cita como confirmada por el paciente.

        Raises:
            ConflictException: Si la cita no esta pendiente.
        """
        if self.status is not AppointmentStatus.PENDING:
            raise ConflictException(
                f"Solo una cita pendiente puede confirmarse; esta esta {self.status.label.lower()}."
            )
        self.status = AppointmentStatus.CONFIRMED

    def complete(self) -> None:
        """Marca la cita como atendida.

        Raises:
            ConflictException: Si la cita ya esta en un estado terminal.
        """
        if self.status.is_final:
            raise ConflictException(f"Una cita {self.status.label.lower()} no puede completarse.")
        self.status = AppointmentStatus.COMPLETED

    def cancel(self) -> None:
        """Cancela la cita y libera el horario del doctor.

        Raises:
            ConflictException: Si la cita ya fue atendida o cancelada.
        """
        if self.status is AppointmentStatus.CANCELLED:
            raise ConflictException("La cita ya estaba cancelada.")
        if self.status is AppointmentStatus.COMPLETED:
            raise ConflictException("Una cita ya atendida no puede cancelarse.")
        self.status = AppointmentStatus.CANCELLED

    def __repr__(self) -> str:
        """Representacion tecnica para bitacoras y depuracion."""
        return (
            f"Appointment(id={self.id}, doctor_id={self.doctor_id}, "
            f"patient_id={self.patient_id}, date={self.slot.date}, "
            f"start={self.slot.start_time}, status={self.status.name})"
        )
