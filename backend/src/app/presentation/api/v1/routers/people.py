"""Endpoints REST de los catalogos de pacientes y doctores.

Exponen el CRUD completo de ambas entidades y, ademas, la agenda asociada a
cada una. La logica de negocio vive en los casos de uso: aqui solo se traduce
HTTP a llamadas y entidades a JSON.
"""

from __future__ import annotations

from datetime import date as Date

from fastapi import APIRouter, Query, Response, status

from app.application.dto.appointment_dto import ListAppointmentsQuery
from app.domain.ports.clock import Clock
from app.presentation.api.errors import NotFoundHTTP
from app.presentation.api.v1.schemas.appointment import AppointmentCollectionResponse
from app.presentation.api.v1.schemas.people import (
    DoctorCreateRequest,
    DoctorResponse,
    DoctorUpdateRequest,
    PatientCreateRequest,
    PatientResponse,
    PatientUpdateRequest,
)
from app.presentation.dependencies import (
    ClockDep,
    CreateDoctorUseCaseDep,
    CreatePatientUseCaseDep,
    DeleteDoctorUseCaseDep,
    DeletePatientUseCaseDep,
    DoctorRepositoryDep,
    PatientRepositoryDep,
    QueryUseCaseDep,
    UpdateDoctorUseCaseDep,
    UpdatePatientUseCaseDep,
)

patients_router = APIRouter(prefix="/patients", tags=["Pacientes"])
doctors_router = APIRouter(prefix="/doctors", tags=["Doctores"])


def _today(clock: Clock) -> Date:
    """Dia actual segun el reloj inyectado."""
    return clock.now().date()


@patients_router.get("", response_model=list[PatientResponse], summary="Listar pacientes")
def list_patients(repository: PatientRepositoryDep, clock: ClockDep) -> list[PatientResponse]:
    """Devuelve el catalogo completo de pacientes."""
    today = _today(clock)
    return [PatientResponse.from_entity(patient, today=today) for patient in repository.list_all()]


@patients_router.post(
    "",
    response_model=PatientResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un paciente",
    responses={422: {"description": "Los datos del paciente no son validos."}},
)
def create_patient(
    payload: PatientCreateRequest, use_case: CreatePatientUseCaseDep, clock: ClockDep
) -> PatientResponse:
    """Da de alta un paciente nuevo."""
    patient = use_case.execute(
        full_name=payload.full_name,
        birth_date=payload.birth_date,
        phone=payload.phone,
    )
    return PatientResponse.from_entity(patient, today=_today(clock))


@patients_router.get(
    "/{patient_id}", response_model=PatientResponse, summary="Consultar un paciente"
)
def get_patient(
    patient_id: int, repository: PatientRepositoryDep, clock: ClockDep
) -> PatientResponse:
    """Devuelve un paciente por su identificador."""
    patient = repository.get(patient_id)
    if patient is None:
        raise NotFoundHTTP(f"Paciente con ID {patient_id} no encontrado.")
    return PatientResponse.from_entity(patient, today=_today(clock))


@patients_router.patch(
    "/{patient_id}",
    response_model=PatientResponse,
    summary="Actualizar un paciente",
    responses={
        404: {"description": "El paciente no existe."},
        422: {"description": "Los datos enviados no son validos."},
    },
)
def update_patient(
    patient_id: int,
    payload: PatientUpdateRequest,
    use_case: UpdatePatientUseCaseDep,
    clock: ClockDep,
) -> PatientResponse:
    """Actualiza los campos enviados; los ausentes se conservan."""
    patient = use_case.execute(
        patient_id,
        full_name=payload.full_name,
        birth_date=payload.birth_date,
        phone=payload.phone,
        clear_phone=payload.clears_phone,
    )
    return PatientResponse.from_entity(patient, today=_today(clock))


@patients_router.delete(
    "/{patient_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un paciente",
    responses={
        404: {"description": "El paciente no existe."},
        409: {"description": "El paciente conserva citas vigentes."},
    },
)
def delete_patient(patient_id: int, use_case: DeletePatientUseCaseDep) -> Response:
    """Elimina al paciente si no tiene citas vigentes."""
    use_case.execute(patient_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


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


@doctors_router.post(
    "",
    response_model=DoctorResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un doctor",
    responses={422: {"description": "Los datos del doctor no son validos."}},
)
def create_doctor(payload: DoctorCreateRequest, use_case: CreateDoctorUseCaseDep) -> DoctorResponse:
    """Da de alta un doctor nuevo."""
    doctor = use_case.execute(
        full_name=payload.full_name,
        speciality=payload.speciality,
        medical_license_number=payload.medical_license_number,
    )
    return DoctorResponse.from_entity(doctor)


@doctors_router.get("/{doctor_id}", response_model=DoctorResponse, summary="Consultar un doctor")
def get_doctor(doctor_id: int, repository: DoctorRepositoryDep) -> DoctorResponse:
    """Devuelve un doctor por su identificador."""
    doctor = repository.get(doctor_id)
    if doctor is None:
        raise NotFoundHTTP(f"Doctor con ID {doctor_id} no encontrado.")
    return DoctorResponse.from_entity(doctor)


@doctors_router.patch(
    "/{doctor_id}",
    response_model=DoctorResponse,
    summary="Actualizar un doctor",
    responses={
        404: {"description": "El doctor no existe."},
        422: {"description": "Los datos enviados no son validos."},
    },
)
def update_doctor(
    doctor_id: int, payload: DoctorUpdateRequest, use_case: UpdateDoctorUseCaseDep
) -> DoctorResponse:
    """Actualiza los campos enviados; los ausentes se conservan."""
    doctor = use_case.execute(
        doctor_id,
        full_name=payload.full_name,
        speciality=payload.speciality,
        medical_license_number=payload.medical_license_number,
        clear_license=payload.clears_license,
    )
    return DoctorResponse.from_entity(doctor)


@doctors_router.delete(
    "/{doctor_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un doctor",
    responses={
        404: {"description": "El doctor no existe."},
        409: {"description": "El doctor conserva citas vigentes."},
    },
)
def delete_doctor(doctor_id: int, use_case: DeleteDoctorUseCaseDep) -> Response:
    """Elimina al doctor si no tiene citas vigentes."""
    use_case.execute(doctor_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


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
