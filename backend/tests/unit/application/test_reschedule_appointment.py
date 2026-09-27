"""Pruebas del caso de uso de reagendado y reasignacion."""

from datetime import time, timedelta

import pytest
from tests.conftest import FUTURE_DATE, make_appointment

from app.application.dto.appointment_dto import RescheduleAppointmentCommand
from app.application.use_cases.reschedule_appointment import RescheduleAppointmentUseCase
from app.domain.entities.appointment import Appointment
from app.domain.exceptions import ConflictException, NotFoundException
from app.domain.value_objects.time_slot import TimeSlot

pytestmark = pytest.mark.unit


@pytest.fixture
def use_case(appointments, patients, doctors, notifier, clock):
    return RescheduleAppointmentUseCase(
        appointments=appointments,
        patients=patients,
        doctors=doctors,
        notifier=notifier,
        clock=clock,
    )


@pytest.fixture
def existing(appointments):
    return appointments.add(make_appointment(doctor_id=1, patient_id=1, hour=10))


def test_changing_the_hour_moves_the_slot(use_case, existing):
    result = use_case.execute(
        RescheduleAppointmentCommand(appointment_id=existing.id, start_time=time(15, 0))
    )

    assert result.appointment.slot.start_time == time(15, 0)


def test_changing_the_hour_notifies_the_patient(use_case, existing, notifier):
    use_case.execute(
        RescheduleAppointmentCommand(appointment_id=existing.id, start_time=time(15, 0))
    )

    assert notifier.call_count == 1


def test_changing_only_the_reason_does_not_notify(use_case, existing, notifier):
    # Corregir una falta de ortografia en el motivo no justifica molestar al
    # paciente con un mensaje.
    use_case.execute(
        RescheduleAppointmentCommand(appointment_id=existing.id, reason="Dolor lumbar persistente")
    )

    assert notifier.call_count == 0


def test_changing_only_the_reason_reports_no_notification(use_case, existing):
    result = use_case.execute(
        RescheduleAppointmentCommand(appointment_id=existing.id, reason="Dolor lumbar persistente")
    )

    assert result.notification_sent is None


def test_reassigning_the_patient_notifies_both(use_case, existing, notifier):
    use_case.execute(RescheduleAppointmentCommand(appointment_id=existing.id, patient_id=2))

    assert notifier.call_count == 2


def test_the_previous_patient_receives_a_cancellation_notice(use_case, existing, notifier):
    use_case.execute(RescheduleAppointmentCommand(appointment_id=existing.id, patient_id=2))

    assert "cancelada" in notifier.sent[0][1]


def test_moving_onto_an_occupied_slot_is_rejected(use_case, appointments, existing):
    appointments.add(make_appointment(doctor_id=1, patient_id=2, hour=12))

    with pytest.raises(ConflictException):
        use_case.execute(
            RescheduleAppointmentCommand(appointment_id=existing.id, start_time=time(12, 0))
        )


def test_an_appointment_does_not_conflict_with_itself(use_case, existing):
    # Reagendar a la misma hora cambiando solo la duracion no debe interpretarse
    # como un choque contra la propia cita.
    result = use_case.execute(
        RescheduleAppointmentCommand(appointment_id=existing.id, duration_minutes=30)
    )

    assert result.appointment.slot.duration_minutes == 30


def test_a_cancelled_appointment_cannot_be_rescheduled(use_case, existing):
    existing.cancel()

    with pytest.raises(ConflictException):
        use_case.execute(
            RescheduleAppointmentCommand(appointment_id=existing.id, start_time=time(15, 0))
        )


def test_unknown_appointment_is_rejected(use_case):
    with pytest.raises(NotFoundException):
        use_case.execute(RescheduleAppointmentCommand(appointment_id=999, start_time=time(15, 0)))


def test_reassigning_to_an_unknown_doctor_is_rejected(use_case, existing):
    with pytest.raises(NotFoundException):
        use_case.execute(RescheduleAppointmentCommand(appointment_id=existing.id, doctor_id=999))


def test_move_to_next_day_shifts_the_date(use_case, existing):
    result = use_case.move_to_next_day(existing.id)

    assert result.appointment.slot.date == FUTURE_DATE + timedelta(days=1)


def test_move_to_next_day_keeps_the_hour(use_case, existing):
    result = use_case.move_to_next_day(existing.id)

    assert result.appointment.slot.start_time == time(10, 0)


def test_move_to_next_day_validates_conflicts(use_case, appointments, existing):
    # El endpoint `move-to-24hours` original no revalidaba la agenda del doctor;
    # aqui si: manana a las 10:00 ya esta ocupado.
    appointments.add(
        Appointment(
            patient_id=2,
            doctor_id=1,
            slot=TimeSlot(
                date=FUTURE_DATE + timedelta(days=1),
                start_time=time(10, 0),
                duration_minutes=60,
            ),
            reason="Otra consulta de control",
        )
    )

    with pytest.raises(ConflictException):
        use_case.move_to_next_day(existing.id)
