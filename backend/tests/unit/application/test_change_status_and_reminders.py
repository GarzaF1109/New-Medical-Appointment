"""Pruebas de transiciones de estado y del envio de recordatorios."""

from datetime import timedelta

import pytest
from tests.conftest import NOW, make_appointment

from app.application.use_cases.change_appointment_status import (
    ChangeAppointmentStatusUseCase,
)
from app.application.use_cases.send_appointment_reminders import (
    SendAppointmentRemindersUseCase,
)
from app.domain.entities.appointment import Appointment, AppointmentStatus
from app.domain.exceptions import ConflictException, NotFoundException
from app.domain.value_objects.time_slot import TimeSlot

pytestmark = pytest.mark.unit


@pytest.fixture
def status_use_case(appointments, patients, doctors, notifier):
    return ChangeAppointmentStatusUseCase(
        appointments=appointments, patients=patients, doctors=doctors, notifier=notifier
    )


def test_cancelling_sets_the_terminal_state(status_use_case, appointments):
    existing = appointments.add(make_appointment())

    result = status_use_case.cancel(existing.id)

    assert result.appointment.status is AppointmentStatus.CANCELLED


def test_cancelling_notifies_the_patient(status_use_case, appointments, notifier):
    existing = appointments.add(make_appointment(patient_id=1))

    status_use_case.cancel(existing.id)

    assert notifier.call_count == 1


def test_completing_does_not_notify(status_use_case, appointments, notifier):
    existing = appointments.add(make_appointment())

    status_use_case.complete(existing.id)

    assert notifier.call_count == 0


def test_completing_a_cancelled_appointment_is_rejected(status_use_case, appointments):
    existing = appointments.add(make_appointment())
    status_use_case.cancel(existing.id)

    with pytest.raises(ConflictException):
        status_use_case.complete(existing.id)


def test_unknown_appointment_is_rejected(status_use_case):
    with pytest.raises(NotFoundException):
        status_use_case.confirm(999)


def tomorrow_appointment(patient_id: int = 1) -> Appointment:
    """Cita pendiente para el dia siguiente al instante congelado."""
    return Appointment(
        patient_id=patient_id,
        doctor_id=1,
        slot=TimeSlot(
            date=(NOW + timedelta(days=1)).date(),
            start_time=NOW.time().replace(hour=11),
        ),
        reason="Consulta de seguimiento",
    )


@pytest.fixture
def reminders_use_case(appointments, patients, doctors, notifier, clock):
    return SendAppointmentRemindersUseCase(
        appointments=appointments,
        patients=patients,
        doctors=doctors,
        notifier=notifier,
        clock=clock,
    )


def test_reminders_reach_tomorrows_patients(reminders_use_case, appointments, notifier):
    appointments.add(tomorrow_appointment(patient_id=1))

    report = reminders_use_case.execute()

    assert report.sent == 1
    assert notifier.call_count == 1


def test_patients_without_phone_are_skipped(reminders_use_case, appointments):
    appointments.add(tomorrow_appointment(patient_id=3))

    report = reminders_use_case.execute()

    assert report.skipped == 1


def test_appointments_on_other_days_are_ignored(reminders_use_case, appointments):
    appointments.add(make_appointment())  # dos semanas despues

    report = reminders_use_case.execute()

    assert report.total == 0


def test_cancelled_appointments_get_no_reminder(reminders_use_case, appointments):
    cancelled = appointments.add(tomorrow_appointment())
    cancelled.cancel()

    report = reminders_use_case.execute()

    assert report.total == 0


def test_provider_failures_are_counted(reminders_use_case, appointments, notifier):
    appointments.add(tomorrow_appointment(patient_id=1))
    notifier.succeeds = False

    report = reminders_use_case.execute()

    assert report.failed == 1
