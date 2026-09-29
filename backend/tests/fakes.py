"""Dobles de prueba en memoria para los puertos del dominio.

Existen gracias a que los casos de uso dependen de interfaces y no de
implementaciones concretas: ninguna prueba unitaria toca la red ni una base de
datos.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import date as Date
from datetime import datetime
from itertools import count

from app.domain.entities.appointment import Appointment, AppointmentStatus
from app.domain.entities.person import Doctor, Patient
from app.domain.ports.clock import Clock
from app.domain.ports.notifications import NotificationSender
from app.domain.ports.repositories import (
    AppointmentRepository,
    DoctorRepository,
    PatientRepository,
)
from app.domain.value_objects.phone_number import PhoneNumber


class FrozenClock(Clock):
    """Reloj detenido en un instante fijo."""

    def __init__(self, moment: datetime) -> None:
        self._moment = moment

    def now(self) -> datetime:
        return self._moment


class SpyNotificationSender(NotificationSender):
    """Notificador que registra los envios en lugar de realizarlos."""

    def __init__(self, *, succeeds: bool = True) -> None:
        self.succeeds = succeeds
        self.sent: list[tuple[str, str]] = []

    def send(self, phone: PhoneNumber, message: str) -> bool:
        self.sent.append((phone.to_e164(), message))
        return self.succeeds

    @property
    def call_count(self) -> int:
        """Numero de mensajes intentados."""
        return len(self.sent)


class InMemoryAppointmentRepository(AppointmentRepository):
    """Repositorio de citas respaldado por un diccionario."""

    def __init__(self, appointments: list[Appointment] | None = None) -> None:
        self._items: dict[int, Appointment] = {}
        self._ids = count(1)
        for appointment in appointments or []:
            self.add(appointment)

    def get(self, appointment_id: int) -> Appointment | None:
        return self._items.get(appointment_id)

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
        matches = [
            a
            for a in self._items.values()
            if (doctor_id is None or a.doctor_id == doctor_id)
            and (patient_id is None or a.patient_id == patient_id)
            and (status is None or a.status == status)
            and (date_from is None or a.slot.date >= date_from)
            and (date_to is None or a.slot.date <= date_to)
        ]
        return matches[offset : offset + limit], len(matches)

    def list_for_doctor_on(self, doctor_id: int, day: Date) -> list[Appointment]:
        return [
            a
            for a in self._items.values()
            if a.doctor_id == doctor_id
            and a.slot.date == day
            and a.status is not AppointmentStatus.CANCELLED
        ]

    def add(self, appointment: Appointment) -> Appointment:
        if appointment.id is None:
            appointment.id = next(self._ids)
        self._items[appointment.id] = appointment
        return appointment

    def update(self, appointment: Appointment) -> Appointment:
        self._items[appointment.id] = appointment
        return appointment

    def delete(self, appointment_id: int) -> None:
        self._items.pop(appointment_id, None)


class InMemoryPatientRepository(PatientRepository):
    """Repositorio de pacientes respaldado por un diccionario."""

    def __init__(self, patients: list[Patient] | None = None) -> None:
        self._items: dict[int, Patient] = {}
        self._ids = count(1)
        for patient in patients or []:
            self.add(patient)

    def get(self, patient_id: int) -> Patient | None:
        return self._items.get(patient_id)

    def list_all(self) -> list[Patient]:
        return sorted(self._items.values(), key=lambda p: p.full_name)

    def add(self, patient: Patient) -> Patient:
        stored = patient if patient.id is not None else replace(patient, id=next(self._ids))
        self._items[stored.id] = stored
        return stored

    def update(self, patient: Patient) -> Patient:
        self._items[patient.id] = patient
        return patient

    def delete(self, patient_id: int) -> None:
        self._items.pop(patient_id, None)


class InMemoryDoctorRepository(DoctorRepository):
    """Repositorio de doctores respaldado por un diccionario."""

    def __init__(self, doctors: list[Doctor] | None = None) -> None:
        self._items: dict[int, Doctor] = {}
        self._ids = count(1)
        for doctor in doctors or []:
            self.add(doctor)

    def get(self, doctor_id: int) -> Doctor | None:
        return self._items.get(doctor_id)

    def list_all(self) -> list[Doctor]:
        return sorted(self._items.values(), key=lambda d: d.full_name)

    def add(self, doctor: Doctor) -> Doctor:
        stored = doctor if doctor.id is not None else replace(doctor, id=next(self._ids))
        self._items[stored.id] = stored
        return stored

    def update(self, doctor: Doctor) -> Doctor:
        self._items[doctor.id] = doctor
        return doctor

    def delete(self, doctor_id: int) -> None:
        self._items.pop(doctor_id, None)
