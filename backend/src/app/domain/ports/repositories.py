"""Puertos de persistencia.

Interfaces que la capa de dominio define y la de infraestructura implementa.
Esto invierte la dependencia (principio D de SOLID): el dominio no importa
SQLAlchemy, es SQLAlchemy quien se adapta al dominio.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date as Date

from app.domain.entities.appointment import Appointment, AppointmentStatus
from app.domain.entities.person import Doctor, Patient


class AppointmentRepository(ABC):
    """Contrato de persistencia para citas."""

    @abstractmethod
    def get(self, appointment_id: int) -> Appointment | None:
        """Recupera una cita por su identificador, o None si no existe."""

    @abstractmethod
    def search(
        self,
        *,
        doctor_id: int | None = None,
        patient_id: int | None = None,
        status: AppointmentStatus | None = None,
        date_from: Date | None = None,
        date_to: Date | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Appointment], int]:
        """Lista citas filtradas y paginadas.

        Returns:
            Una tupla (pagina de resultados, total de coincidencias sin paginar).
        """

    @abstractmethod
    def list_for_doctor_on(self, doctor_id: int, day: Date) -> list[Appointment]:
        """Devuelve la agenda de un doctor en un dia dado.

        Se usa para detectar conflictos de horario. Devuelve entidades -no un
        booleano- para que la regla de solapamiento se evalue en el dominio y no
        en una consulta SQL, donde seria imposible probarla de forma aislada.
        """

    @abstractmethod
    def add(self, appointment: Appointment) -> Appointment:
        """Persiste una cita nueva y devuelve la instancia con su ID asignado."""

    @abstractmethod
    def update(self, appointment: Appointment) -> Appointment:
        """Persiste los cambios de una cita existente."""

    @abstractmethod
    def delete(self, appointment_id: int) -> None:
        """Elimina una cita de forma definitiva."""


class PatientRepository(ABC):
    """Contrato de persistencia para pacientes."""

    @abstractmethod
    def get(self, patient_id: int) -> Patient | None:
        """Recupera un paciente por su identificador, o None si no existe."""

    @abstractmethod
    def list_all(self) -> list[Patient]:
        """Devuelve todos los pacientes, ordenados por nombre."""

    @abstractmethod
    def add(self, patient: Patient) -> Patient:
        """Persiste un paciente nuevo y devuelve la instancia con su ID."""

    @abstractmethod
    def update(self, patient: Patient) -> Patient:
        """Persiste los cambios de un paciente existente."""

    @abstractmethod
    def delete(self, patient_id: int) -> None:
        """Elimina un paciente de forma definitiva."""


class DoctorRepository(ABC):
    """Contrato de persistencia para doctores."""

    @abstractmethod
    def get(self, doctor_id: int) -> Doctor | None:
        """Recupera un doctor por su identificador, o None si no existe."""

    @abstractmethod
    def list_all(self) -> list[Doctor]:
        """Devuelve todos los doctores, ordenados por nombre."""

    @abstractmethod
    def add(self, doctor: Doctor) -> Doctor:
        """Persiste un doctor nuevo y devuelve la instancia con su ID."""

    @abstractmethod
    def update(self, doctor: Doctor) -> Doctor:
        """Persiste los cambios de un doctor existente."""

    @abstractmethod
    def delete(self, doctor_id: int) -> None:
        """Elimina un doctor de forma definitiva."""
