"""Pruebas del caso de uso de agendado."""

from datetime import time

import pytest
from tests.conftest import FUTURE_DATE, make_appointment

from app.application.dto.appointment_dto import ScheduleAppointmentCommand
from app.application.use_cases.schedule_appointment import ScheduleAppointmentUseCase
from app.domain.exceptions import ConflictException, InvalidInputException, NotFoundException

pytestmark = pytest.mark.unit


@pytest.fixture
def use_case(appointments, patients, doctors, notifier, clock):
    return ScheduleAppointmentUseCase(
        appointments=appointments,
        patients=patients,
        doctors=doctors,
        notifier=notifier,
        clock=clock,
    )


def command(**overrides) -> ScheduleAppointmentCommand:
    defaults = {
        "patient_id": 1,
        "doctor_id": 1,
        "date": FUTURE_DATE,
        "start_time": time(10, 0),
        "reason": "Dolor de cabeza persistente",
    }
    return ScheduleAppointmentCommand(**{**defaults, **overrides})


def test_scheduling_persists_the_appointment(use_case, appointments):
    result = use_case.execute(command())

    assert appointments.get(result.appointment.id) is not None


def test_scheduling_notifies_a_reachable_patient(use_case, notifier):
    use_case.execute(command(patient_id=1))

    assert notifier.call_count == 1


def test_the_message_names_the_doctor(use_case, notifier):
    use_case.execute(command(doctor_id=1))

    assert "Dr(a). Elena Navarro" in notifier.sent[0][1]


def test_a_patient_without_phone_is_not_notified(use_case, notifier):
    result = use_case.execute(command(patient_id=3))

    assert notifier.call_count == 0
    assert result.notification_sent is False


def test_the_appointment_survives_a_failed_notification(use_case, notifier, appointments):
    # Una caida del proveedor de mensajeria no debe perder la cita del paciente.
    notifier.succeeds = False

    result = use_case.execute(command())

    assert appointments.get(result.appointment.id) is not None
    assert result.notification_sent is False


def test_unknown_patient_is_rejected(use_case):
    with pytest.raises(NotFoundException):
        use_case.execute(command(patient_id=999))


def test_unknown_doctor_is_rejected(use_case):
    with pytest.raises(NotFoundException):
        use_case.execute(command(doctor_id=999))


def test_double_booking_the_same_doctor_is_rejected(use_case, appointments):
    appointments.add(make_appointment(doctor_id=1, hour=10))

    with pytest.raises(ConflictException):
        use_case.execute(command(doctor_id=1, start_time=time(10, 30)))


def test_a_cancelled_appointment_frees_the_slot(use_case, appointments):
    existing = appointments.add(make_appointment(doctor_id=1, hour=10))
    existing.cancel()

    result = use_case.execute(command(doctor_id=1, start_time=time(10, 0)))

    assert result.appointment.id is not None


def test_back_to_back_appointments_are_allowed(use_case, appointments):
    appointments.add(make_appointment(doctor_id=1, hour=10))

    result = use_case.execute(command(doctor_id=1, start_time=time(11, 0)))

    assert result.appointment.slot.start_time == time(11, 0)


def test_two_doctors_can_share_the_same_hour(use_case, appointments):
    appointments.add(make_appointment(doctor_id=1, hour=10))

    result = use_case.execute(command(doctor_id=2, start_time=time(10, 0)))

    assert result.appointment.doctor_id == 2


def test_a_short_reason_is_rejected(use_case):
    with pytest.raises(InvalidInputException):
        use_case.execute(command(reason="gripa"))


def test_the_result_carries_resolved_names(use_case):
    result = use_case.execute(command(patient_id=2, doctor_id=2))

    assert result.patient_name == "Carlos Ramirez"
    assert result.doctor_name == "Dr(a). Roberto Diaz"
