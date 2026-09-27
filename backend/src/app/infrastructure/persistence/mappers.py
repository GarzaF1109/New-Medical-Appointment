"""Traduccion entre modelos de persistencia y entidades de dominio."""

from __future__ import annotations

from app.domain.entities.appointment import Appointment, AppointmentStatus
from app.domain.entities.person import Doctor, Patient
from app.domain.exceptions import InvalidInputException
from app.domain.value_objects.birth_date import BirthDate
from app.domain.value_objects.medical_license import MedicalLicense
from app.domain.value_objects.phone_number import PhoneNumber
from app.domain.value_objects.time_slot import TimeSlot
from app.infrastructure.persistence.models import (
    AppointmentModel,
    DoctorModel,
    PatientModel,
)


def appointment_to_domain(model: AppointmentModel) -> Appointment:
    """Convierte una fila de `appointments` en una entidad Appointment."""
    return Appointment(
        id=model.id,
        patient_id=model.patient_id,
        doctor_id=model.doctor_id,
        slot=TimeSlot(
            date=model.date,
            start_time=model.start_time,
            duration_minutes=model.duration_minutes,
        ),
        reason=model.reason,
        status=AppointmentStatus(model.status),
    )


def appointment_to_model(
    entity: Appointment, model: AppointmentModel | None = None
) -> AppointmentModel:
    """Vuelca una entidad Appointment sobre una fila, creandola si hace falta."""
    target = model or AppointmentModel()
    target.patient_id = entity.patient_id
    target.doctor_id = entity.doctor_id
    target.date = entity.slot.date
    target.start_time = entity.slot.start_time
    target.duration_minutes = entity.slot.duration_minutes
    target.reason = entity.reason
    target.status = int(entity.status)
    return target


def patient_to_domain(model: PatientModel) -> Patient:
    """Convierte una fila de `patients` en una entidad Patient.

    Un telefono almacenado con formato invalido no debe tumbar la lectura: se
    trata como paciente sin telefono, que el dominio ya sabe manejar.
    """
    phone: PhoneNumber | None = None
    if model.phone:
        try:
            phone = PhoneNumber.parse(model.phone)
        except InvalidInputException:
            phone = None
    return Patient(
        id=model.id,
        full_name=model.full_name,
        birth_date=BirthDate(model.birth_date),
        phone=phone,
    )


def patient_to_model(entity: Patient, model: PatientModel | None = None) -> PatientModel:
    """Vuelca una entidad Patient sobre una fila, creandola si hace falta."""
    target = model or PatientModel()
    target.full_name = entity.full_name
    target.birth_date = entity.birth_date.value
    target.phone = entity.phone.value if entity.phone else None
    return target


def doctor_to_domain(model: DoctorModel) -> Doctor:
    """Convierte una fila de `doctors` en una entidad Doctor."""
    license_: MedicalLicense | None = None
    if model.medical_license_number:
        try:
            license_ = MedicalLicense(model.medical_license_number)
        except InvalidInputException:
            license_ = None
    return Doctor(
        id=model.id,
        full_name=model.full_name,
        speciality=model.speciality,
        license=license_,
    )


def doctor_to_model(entity: Doctor, model: DoctorModel | None = None) -> DoctorModel:
    """Vuelca una entidad Doctor sobre una fila, creandola si hace falta."""
    target = model or DoctorModel()
    target.full_name = entity.full_name
    target.speciality = entity.speciality
    target.medical_license_number = str(entity.license) if entity.license else None
    return target
