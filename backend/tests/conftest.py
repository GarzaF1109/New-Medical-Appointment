"""Fixtures compartidas por toda la suite."""

from __future__ import annotations

from datetime import date, datetime, time

import pytest

from app.domain.entities.appointment import Appointment
from app.domain.entities.person import Doctor, Patient
from app.domain.value_objects.phone_number import PhoneNumber
from app.domain.value_objects.time_slot import TimeSlot
from tests.fakes import (
    FrozenClock,
    InMemoryAppointmentRepository,
    InMemoryDoctorRepository,
    InMemoryPatientRepository,
    SpyNotificationSender,
)

# Instante de referencia de toda la suite. Fijarlo hace que las pruebas de
# reglas temporales no cambien de resultado segun el dia en que se ejecuten.
NOW = datetime(2026, 10, 1, 9, 0)
FUTURE_DATE = date(2026, 10, 15)


@pytest.fixture
def clock() -> FrozenClock:
    return FrozenClock(NOW)


@pytest.fixture
def notifier() -> SpyNotificationSender:
    return SpyNotificationSender()


@pytest.fixture
def patients() -> InMemoryPatientRepository:
    return InMemoryPatientRepository(
        [
            Patient(id=1, full_name="Ana Maria Lopez", phone=PhoneNumber.parse("8112345678")),
            Patient(id=2, full_name="Carlos Ramirez", phone=PhoneNumber.parse("8187654321")),
            Patient(id=3, full_name="Lucia Sin Telefono", phone=None),
        ]
    )


@pytest.fixture
def doctors() -> InMemoryDoctorRepository:
    return InMemoryDoctorRepository(
        [
            Doctor(id=1, full_name="Elena Navarro", speciality="Cardiologia"),
            Doctor(id=2, full_name="Roberto Diaz", speciality="Pediatria"),
        ]
    )


@pytest.fixture
def appointments() -> InMemoryAppointmentRepository:
    return InMemoryAppointmentRepository()


def make_slot(hour: int = 10, minute: int = 0, duration: int = 60) -> TimeSlot:
    """Construye una franja en la fecha futura de referencia."""
    return TimeSlot(date=FUTURE_DATE, start_time=time(hour, minute), duration_minutes=duration)


def make_appointment(
    *, doctor_id: int = 1, patient_id: int = 1, hour: int = 10, id: int | None = None
) -> Appointment:
    """Construye una cita valida para las pruebas."""
    return Appointment(
        id=id,
        patient_id=patient_id,
        doctor_id=doctor_id,
        slot=make_slot(hour),
        reason="Consulta de control periodico",
    )
