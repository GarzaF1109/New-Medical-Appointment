"""Pruebas de la entidad Cita: invariantes y transiciones de estado."""

from datetime import datetime

import pytest
from tests.conftest import NOW, make_appointment, make_slot

from app.domain.entities.appointment import Appointment, AppointmentStatus
from app.domain.exceptions import ConflictException, InvalidInputException

pytestmark = pytest.mark.unit


def test_a_new_appointment_starts_pending():
    appointment = Appointment.schedule(
        patient_id=1, doctor_id=1, slot=make_slot(), reason="Revision anual de rutina", now=NOW
    )

    assert appointment.status is AppointmentStatus.PENDING


def test_cannot_schedule_in_the_past():
    with pytest.raises(InvalidInputException):
        Appointment.schedule(
            patient_id=1,
            doctor_id=1,
            slot=make_slot(),
            reason="Revision anual de rutina",
            now=datetime(2027, 1, 1, 9, 0),
        )


def test_reason_shorter_than_the_minimum_is_rejected():
    with pytest.raises(InvalidInputException):
        make_appointment().change_reason("gripa")


def test_reason_is_trimmed():
    appointment = make_appointment()

    appointment.change_reason("   Dolor lumbar persistente   ")

    assert appointment.reason == "Dolor lumbar persistente"


def test_same_doctor_overlapping_slots_conflict():
    existing = make_appointment(doctor_id=1, hour=10, id=1)
    candidate = make_appointment(doctor_id=1, hour=10)

    assert candidate.conflicts_with(existing) is True


def test_different_doctors_never_conflict():
    existing = make_appointment(doctor_id=1, hour=10, id=1)
    candidate = make_appointment(doctor_id=2, hour=10)

    assert candidate.conflicts_with(existing) is False


def test_a_cancelled_appointment_frees_its_slot():
    existing = make_appointment(doctor_id=1, hour=10, id=1)
    existing.cancel()
    candidate = make_appointment(doctor_id=1, hour=10)

    assert candidate.conflicts_with(existing) is False


def test_an_appointment_never_conflicts_with_itself():
    appointment = make_appointment(id=7)

    assert appointment.conflicts_with(appointment) is False


def test_pending_appointment_can_be_confirmed():
    appointment = make_appointment()

    appointment.confirm()

    assert appointment.status is AppointmentStatus.CONFIRMED


def test_confirming_twice_is_rejected():
    appointment = make_appointment()
    appointment.confirm()

    with pytest.raises(ConflictException):
        appointment.confirm()


def test_completed_appointment_cannot_be_cancelled():
    appointment = make_appointment()
    appointment.complete()

    with pytest.raises(ConflictException):
        appointment.cancel()


def test_cancelling_twice_is_rejected():
    appointment = make_appointment()
    appointment.cancel()

    with pytest.raises(ConflictException):
        appointment.cancel()


def test_cancelled_appointment_cannot_be_rescheduled():
    appointment = make_appointment()
    appointment.cancel()

    with pytest.raises(ConflictException):
        appointment.reschedule(make_slot(hour=12), NOW)


def test_rescheduling_to_the_past_is_rejected():
    appointment = make_appointment()

    with pytest.raises(InvalidInputException):
        appointment.reschedule(make_slot(hour=12), datetime(2027, 1, 1, 9, 0))


def test_reschedule_moves_the_slot():
    appointment = make_appointment(hour=10)

    appointment.reschedule(make_slot(hour=15), NOW)

    assert appointment.slot.start_time.hour == 15


def test_status_labels_are_in_spanish():
    assert AppointmentStatus.PENDING.label == "Pendiente"


def test_terminal_states_are_marked_as_final():
    assert AppointmentStatus.COMPLETED.is_final is True
    assert AppointmentStatus.PENDING.is_final is False
