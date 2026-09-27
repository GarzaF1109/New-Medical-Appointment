"""Pruebas de la traduccion entre filas y entidades de dominio."""

from datetime import date, time

import pytest

from app.domain.entities.appointment import AppointmentStatus
from app.domain.exceptions import InvalidInputException
from app.domain.value_objects.medical_license import MedicalLicense
from app.infrastructure.persistence.mappers import (
    appointment_to_domain,
    appointment_to_model,
    doctor_to_domain,
    patient_to_domain,
)
from app.infrastructure.persistence.models import (
    AppointmentModel,
    DoctorModel,
    PatientModel,
)

pytestmark = pytest.mark.unit


def row() -> AppointmentModel:
    return AppointmentModel(
        id=7,
        patient_id=1,
        doctor_id=2,
        date=date(2026, 10, 15),
        start_time=time(10, 0),
        duration_minutes=45,
        reason="Consulta de control periodico",
        status=2,
    )


def test_a_row_becomes_an_entity_with_its_slot():
    entity = appointment_to_domain(row())

    assert entity.slot.end_time == time(10, 45)


def test_the_numeric_status_becomes_an_enum():
    assert appointment_to_domain(row()).status is AppointmentStatus.CONFIRMED


def test_an_entity_writes_back_onto_its_row():
    entity = appointment_to_domain(row())
    entity.cancel()

    model = appointment_to_model(entity, row())

    assert model.status == int(AppointmentStatus.CANCELLED)


def test_a_valid_phone_is_parsed_on_read():
    patient = patient_to_domain(
        PatientModel(id=1, full_name="Ana", birth_date=date(1990, 5, 20), phone="8112345678")
    )

    assert patient.phone.value == "5218112345678"


def test_a_corrupt_phone_degrades_to_none():
    # Un dato heredado invalido no debe impedir leer al paciente.
    patient = patient_to_domain(
        PatientModel(id=1, full_name="Ana", birth_date=date(1990, 5, 20), phone="123")
    )

    assert patient.phone is None


def test_a_missing_phone_marks_the_patient_unreachable():
    patient = patient_to_domain(
        PatientModel(id=1, full_name="Ana", birth_date=date(1990, 5, 20), phone=None)
    )

    assert patient.is_reachable is False


def test_a_valid_license_is_parsed_on_read():
    doctor = doctor_to_domain(
        DoctorModel(
            id=1,
            full_name="Elena",
            speciality="Cardiologia",
            medical_license_number="L-20260526-8845A",
        )
    )

    assert str(doctor.license) == "L-20260526-8845A"


def test_a_malformed_license_degrades_to_none():
    doctor = doctor_to_domain(
        DoctorModel(id=1, full_name="Elena", speciality="Cardiologia", medical_license_number="ABC")
    )

    assert doctor.license is None


def test_the_display_name_prefixes_the_title():
    doctor = doctor_to_domain(
        DoctorModel(id=1, full_name="Elena Navarro", speciality="Cardiologia")
    )

    assert doctor.display_name == "Dr(a). Elena Navarro"


def test_a_malformed_license_is_rejected_at_construction():
    with pytest.raises(InvalidInputException):
        MedicalLicense("L-2026-88A")
