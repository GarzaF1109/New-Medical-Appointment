"""Endpoints REST de los catalogos de pacientes y doctores.

Son de solo lectura en este slice: alimentan los selectores del formulario de
citas. Los CRUD completos llegaran con los slices de Pacientes y Doctores.
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.application.dto.appointment_dto import ListAppointmentsQuery
from app.presentation.api.errors import NotFoundHTTP
from app.presentation.api.v1.schemas.appointment import AppointmentCollectionResponse
from app.presentation.api.v1.schemas.people import DoctorResponse, PatientResponse
from app.presentation.dependencies import (
    DoctorRepositoryDep,
    PatientRepositoryDep,
    QueryUseCaseDep,
)

patients_router = APIRouter(prefix="/patients", tags=["Pacientes"])
doctors_router = APIRouter(prefix="/doctors", tags=["Doctores"])


@patients_router.get("", response_model=list[PatientResponse], summary="Listar pacientes")
def list_patients(repository: PatientRepositoryDep) -> list[PatientResponse]:
    """Devuelve el catalogo completo de pacientes."""
    return [PatientResponse.from_entity(patient) for patient in repository.list_all()]


@patients_router.get(
    "/{patient_id}", response_model=PatientResponse, summary="Consultar un paciente"
)
def get_patient(patient_id: int, repository: PatientRepositoryDep) -> PatientResponse:
    """Devuelve un paciente por su identificador."""
    patient = repository.get(patient_id)
    if patient is None:
        raise NotFoundHTTP(f"Paciente con ID {patient_id} no encontrado.")
    return PatientResponse.from_entity(patient)


@patients_router.get(
    "/{patient_id}/appointments",
    response_model=AppointmentCollectionResponse,
    summary="Listar las citas de un paciente",
)
def list_patient_appointments(
    patient_id: int,
    use_case: QueryUseCaseDep,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> AppointmentCollectionResponse:
    """Devuelve el historial de citas del paciente."""
    page = use_case.list(ListAppointmentsQuery(patient_id=patient_id, limit=limit, offset=offset))
    return AppointmentCollectionResponse.from_page(page)


@doctors_router.get("", response_model=list[DoctorResponse], summary="Listar doctores")
def list_doctors(repository: DoctorRepositoryDep) -> list[DoctorResponse]:
    """Devuelve el catalogo completo de doctores."""
    return [DoctorResponse.from_entity(doctor) for doctor in repository.list_all()]


@doctors_router.get("/{doctor_id}", response_model=DoctorResponse, summary="Consultar un doctor")
def get_doctor(doctor_id: int, repository: DoctorRepositoryDep) -> DoctorResponse:
    """Devuelve un doctor por su identificador."""
    doctor = repository.get(doctor_id)
    if doctor is None:
        raise NotFoundHTTP(f"Doctor con ID {doctor_id} no encontrado.")
    return DoctorResponse.from_entity(doctor)


@doctors_router.get(
    "/{doctor_id}/appointments",
    response_model=AppointmentCollectionResponse,
    summary="Consultar la agenda de un doctor",
)
def list_doctor_appointments(
    doctor_id: int,
    use_case: QueryUseCaseDep,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> AppointmentCollectionResponse:
    """Devuelve la agenda del doctor."""
    page = use_case.list(ListAppointmentsQuery(doctor_id=doctor_id, limit=limit, offset=offset))
    return AppointmentCollectionResponse.from_page(page)
