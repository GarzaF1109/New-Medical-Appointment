"""Pruebas de las entidades Paciente y Doctor."""

from datetime import date

import pytest

from app.domain.entities.person import Doctor, Patient
from app.domain.exceptions import InvalidInputException
from app.domain.value_objects.birth_date import BirthDate
from app.domain.value_objects.medical_license import MedicalLicense
from app.domain.value_objects.phone_number import PhoneNumber

TODAY = date(2026, 10, 1)
BIRTH = BirthDate(date(1988, 3, 14))


def make_patient(**overrides) -> Patient:
    defaults = {"id": 1, "full_name": "Ana Maria Lopez", "birth_date": BIRTH, "phone": None}
    return Patient(**{**defaults, **overrides})


def make_doctor(**overrides) -> Doctor:
    defaults = {"id": 1, "full_name": "Elena Navarro", "speciality": "Cardiologia"}
    return Doctor(**{**defaults, **overrides})


def test_the_patient_name_is_trimmed():
    assert make_patient(full_name="  Ana Maria Lopez  ").full_name == "Ana Maria Lopez"


def test_a_too_short_patient_name_is_rejected():
    with pytest.raises(InvalidInputException, match="nombre"):
        make_patient(full_name="Al")


def test_a_blank_patient_name_is_rejected():
    with pytest.raises(InvalidInputException):
        make_patient(full_name="   ")


def test_a_patient_without_phone_is_not_reachable():
    assert make_patient(phone=None).is_reachable is False


def test_a_patient_with_phone_is_reachable():
    assert make_patient(phone=PhoneNumber.parse("8112345678")).is_reachable is True


def test_the_patient_exposes_its_age():
    assert make_patient().age_on(TODAY) == 38


def test_editing_a_patient_returns_a_new_instance():
    original = make_patient()

    updated = original.with_changes(full_name="Ana Maria Lopez Garza")

    assert updated.full_name == "Ana Maria Lopez Garza"
    assert original.full_name == "Ana Maria Lopez"


def test_editing_keeps_the_fields_that_were_not_sent():
    original = make_patient(phone=PhoneNumber.parse("8112345678"))

    updated = original.with_changes(full_name="Ana Lopez")

    assert updated.phone == original.phone
    assert updated.birth_date == original.birth_date


def test_a_patient_phone_can_be_cleared_explicitly():
    original = make_patient(phone=PhoneNumber.parse("8112345678"))

    assert original.with_changes(clear_phone=True).phone is None


def test_an_invalid_edit_never_produces_a_half_updated_patient():
    original = make_patient()

    with pytest.raises(InvalidInputException):
        original.with_changes(full_name="Al")

    assert original.full_name == "Ana Maria Lopez"


def test_the_doctor_display_name_prefixes_the_title():
    assert make_doctor().display_name == "Dr(a). Elena Navarro"


def test_a_blank_speciality_is_rejected():
    with pytest.raises(InvalidInputException, match="especialidad"):
        make_doctor(speciality="  ")


def test_editing_a_doctor_returns_a_new_instance():
    original = make_doctor()

    updated = original.with_changes(speciality="Cardiologia Pediatrica")

    assert updated.speciality == "Cardiologia Pediatrica"
    assert original.speciality == "Cardiologia"


def test_a_doctor_license_can_be_cleared_explicitly():
    original = make_doctor(license=MedicalLicense("L-20260526-8845A"))

    assert original.with_changes(clear_license=True).license is None
