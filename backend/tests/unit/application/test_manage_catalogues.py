"""Pruebas de los casos de uso de alta, edicion y baja de pacientes y doctores."""

from datetime import date

import pytest
from tests.conftest import NOW, make_appointment
from tests.fakes import FrozenClock

from app.application.use_cases.manage_doctors import (
    CreateDoctorUseCase,
    DeleteDoctorUseCase,
    UpdateDoctorUseCase,
)
from app.application.use_cases.manage_patients import (
    CreatePatientUseCase,
    DeletePatientUseCase,
    UpdatePatientUseCase,
)
from app.domain.exceptions import ConflictException, InvalidInputException, NotFoundException

BIRTH = date(1988, 3, 14)


@pytest.fixture
def clock() -> FrozenClock:
    return FrozenClock(NOW)


# --- Pacientes -------------------------------------------------------------


def test_creating_a_patient_assigns_an_id(patients, clock):
    use_case = CreatePatientUseCase(patients=patients, clock=clock)

    created = use_case.execute(full_name="Sofia Herrera", birth_date=BIRTH)

    assert created.id is not None
    assert patients.get(created.id).full_name == "Sofia Herrera"


def test_creating_a_patient_normalises_the_phone(patients, clock):
    use_case = CreatePatientUseCase(patients=patients, clock=clock)

    created = use_case.execute(full_name="Sofia Herrera", birth_date=BIRTH, phone="811 234 5678")

    assert created.phone.value == "5218112345678"


def test_a_patient_born_in_the_future_is_rejected(patients, clock):
    use_case = CreatePatientUseCase(patients=patients, clock=clock)

    with pytest.raises(InvalidInputException, match="futuro"):
        use_case.execute(full_name="Sofia Herrera", birth_date=date(2027, 1, 1))


def test_an_impossible_age_is_rejected(patients, clock):
    use_case = CreatePatientUseCase(patients=patients, clock=clock)

    with pytest.raises(InvalidInputException, match="edad"):
        use_case.execute(full_name="Sofia Herrera", birth_date=date(1900, 1, 1))


def test_updating_a_patient_changes_only_what_was_sent(patients, clock):
    use_case = UpdatePatientUseCase(patients=patients, clock=clock)
    before = patients.get(1)

    updated = use_case.execute(1, full_name="Ana Maria Lopez Garza")

    assert updated.full_name == "Ana Maria Lopez Garza"
    assert updated.phone == before.phone
    assert updated.birth_date == before.birth_date


def test_updating_a_patient_can_clear_the_phone(patients, clock):
    use_case = UpdatePatientUseCase(patients=patients, clock=clock)

    assert use_case.execute(1, clear_phone=True).phone is None


def test_updating_an_unknown_patient_raises_not_found(patients, clock):
    use_case = UpdatePatientUseCase(patients=patients, clock=clock)

    with pytest.raises(NotFoundException):
        use_case.execute(999, full_name="Nadie Aqui")


def test_a_patient_without_appointments_can_be_deleted(patients, appointments):
    use_case = DeletePatientUseCase(patients=patients, appointments=appointments)

    use_case.execute(1)

    assert patients.get(1) is None


def test_deleting_an_unknown_patient_raises_not_found(patients, appointments):
    use_case = DeletePatientUseCase(patients=patients, appointments=appointments)

    with pytest.raises(NotFoundException):
        use_case.execute(999)


def test_a_patient_with_a_live_appointment_cannot_be_deleted(patients, appointments):
    appointments.add(make_appointment(patient_id=1))
    use_case = DeletePatientUseCase(patients=patients, appointments=appointments)

    with pytest.raises(ConflictException, match="citas vigentes"):
        use_case.execute(1)

    assert patients.get(1) is not None


def test_a_cancelled_appointment_does_not_block_deletion(patients, appointments):
    appointment = make_appointment(patient_id=1)
    appointment.cancel()
    appointments.add(appointment)
    use_case = DeletePatientUseCase(patients=patients, appointments=appointments)

    use_case.execute(1)

    assert patients.get(1) is None


def test_another_patients_appointment_does_not_block_deletion(patients, appointments):
    appointments.add(make_appointment(patient_id=2))
    use_case = DeletePatientUseCase(patients=patients, appointments=appointments)

    use_case.execute(1)

    assert patients.get(1) is None


# --- Doctores --------------------------------------------------------------


def test_creating_a_doctor_assigns_an_id(doctors):
    use_case = CreateDoctorUseCase(doctors=doctors)

    created = use_case.execute(full_name="Sofia Herrera", speciality="Medicina General")

    assert created.id is not None
    assert doctors.get(created.id).speciality == "Medicina General"


def test_creating_a_doctor_validates_the_license_format(doctors):
    use_case = CreateDoctorUseCase(doctors=doctors)

    with pytest.raises(InvalidInputException, match="licencia"):
        use_case.execute(
            full_name="Sofia Herrera",
            speciality="Medicina General",
            medical_license_number="ABC-123",
        )


def test_updating_a_doctor_changes_only_what_was_sent(doctors):
    use_case = UpdateDoctorUseCase(doctors=doctors)

    updated = use_case.execute(1, speciality="Cardiologia Pediatrica")

    assert updated.speciality == "Cardiologia Pediatrica"
    assert updated.full_name == "Elena Navarro"


def test_updating_an_unknown_doctor_raises_not_found(doctors):
    use_case = UpdateDoctorUseCase(doctors=doctors)

    with pytest.raises(NotFoundException):
        use_case.execute(999, speciality="Pediatria")


def test_a_doctor_without_appointments_can_be_deleted(doctors, appointments):
    use_case = DeleteDoctorUseCase(doctors=doctors, appointments=appointments)

    use_case.execute(1)

    assert doctors.get(1) is None


def test_deleting_an_unknown_doctor_raises_not_found(doctors, appointments):
    use_case = DeleteDoctorUseCase(doctors=doctors, appointments=appointments)

    with pytest.raises(NotFoundException):
        use_case.execute(999)


def test_a_doctor_with_a_live_appointment_cannot_be_deleted(doctors, appointments):
    appointments.add(make_appointment(doctor_id=1))
    use_case = DeleteDoctorUseCase(doctors=doctors, appointments=appointments)

    with pytest.raises(ConflictException, match="citas vigentes"):
        use_case.execute(1)

    assert doctors.get(1) is not None


def test_a_completed_appointment_does_not_block_doctor_deletion(doctors, appointments):
    appointment = make_appointment(doctor_id=1)
    appointment.complete()
    appointments.add(appointment)
    use_case = DeleteDoctorUseCase(doctors=doctors, appointments=appointments)

    use_case.execute(1)

    assert doctors.get(1) is None
