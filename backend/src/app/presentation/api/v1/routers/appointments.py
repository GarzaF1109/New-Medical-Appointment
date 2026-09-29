"""Endpoints REST del recurso Citas.

Diseno de URI segun la guia AIVARA: sustantivos en plural, jerarquia para
recursos relacionados y parametros de consulta para filtrado y paginacion. Las
transiciones de estado se modelan como subrecursos (`/cancellation`) en lugar
de verbos en la ruta.
"""

from __future__ import annotations

from datetime import date as Date
from typing import Any

from fastapi import APIRouter, Query, Response, status

from app.application.dto.appointment_dto import (
    ListAppointmentsQuery,
    RescheduleAppointmentCommand,
    ScheduleAppointmentCommand,
)
from app.domain.entities.appointment import AppointmentStatus
from app.presentation.api.v1.schemas.appointment import (
    AppointmentCollectionResponse,
    AppointmentResponse,
    ErrorResponse,
    RescheduleAppointmentRequest,
    ScheduleAppointmentRequest,
)
from app.presentation.dependencies import (
    DeleteUseCaseDep,
    QueryUseCaseDep,
    RescheduleUseCaseDep,
    ScheduleUseCaseDep,
    StatusUseCaseDep,
)

router = APIRouter(prefix="/appointments", tags=["Citas"])

# FastAPI acepta int o str como clave de `responses`; anotarlo explicitamente
# evita que el tipo se infiera como `dict[int, ...]`, mas estrecho de la cuenta.
_COMMON_ERRORS: dict[int | str, dict[str, Any]] = {
    404: {"model": ErrorResponse, "description": "La cita no existe"},
    422: {"model": ErrorResponse, "description": "Datos de entrada invalidos"},
}


@router.get(
    "",
    response_model=AppointmentCollectionResponse,
    summary="Listar citas",
    description="Devuelve una pagina de citas. Todos los filtros son opcionales y combinables.",
)
def list_appointments(
    use_case: QueryUseCaseDep,
    doctor_id: int | None = Query(default=None, alias="doctorId", gt=0),
    patient_id: int | None = Query(default=None, alias="patientId", gt=0),
    status_filter: AppointmentStatus | None = Query(default=None, alias="status"),
    date_from: Date | None = Query(default=None, alias="dateFrom"),
    date_to: Date | None = Query(default=None, alias="dateTo"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> AppointmentCollectionResponse:
    """Lista citas filtradas y paginadas."""
    page = use_case.search(
        ListAppointmentsQuery(
            doctor_id=doctor_id,
            patient_id=patient_id,
            status=status_filter,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
            offset=offset,
        )
    )
    return AppointmentCollectionResponse.from_page(page)


@router.post(
    "",
    response_model=AppointmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Agendar una cita",
    responses={
        409: {"model": ErrorResponse, "description": "El doctor ya tiene una cita en ese horario"},
        **_COMMON_ERRORS,
    },
)
def schedule_appointment(
    payload: ScheduleAppointmentRequest, use_case: ScheduleUseCaseDep
) -> AppointmentResponse:
    """Agenda una cita nueva y notifica al paciente."""
    result = use_case.execute(
        ScheduleAppointmentCommand(
            patient_id=payload.patient_id,
            doctor_id=payload.doctor_id,
            date=payload.date,
            start_time=payload.start_time,
            duration_minutes=payload.duration_minutes,
            reason=payload.reason,
        )
    )
    return AppointmentResponse.from_result(result)


@router.get(
    "/{appointment_id}",
    response_model=AppointmentResponse,
    summary="Consultar una cita",
    responses=_COMMON_ERRORS,
)
def get_appointment(appointment_id: int, use_case: QueryUseCaseDep) -> AppointmentResponse:
    """Devuelve una cita por su identificador."""
    return AppointmentResponse.from_result(use_case.get(appointment_id))


@router.patch(
    "/{appointment_id}",
    response_model=AppointmentResponse,
    summary="Reagendar o reasignar una cita",
    description=(
        "Actualiza parcialmente una cita. Solo se notifica al paciente cuando el "
        "cambio le afecta: horario, doctor o reasignacion a otro paciente."
    ),
    responses={
        409: {"model": ErrorResponse, "description": "Conflicto de horario o estado terminal"},
        **_COMMON_ERRORS,
    },
)
def reschedule_appointment(
    appointment_id: int,
    payload: RescheduleAppointmentRequest,
    use_case: RescheduleUseCaseDep,
) -> AppointmentResponse:
    """Aplica cambios parciales sobre una cita existente."""
    result = use_case.execute(
        RescheduleAppointmentCommand(
            appointment_id=appointment_id,
            date=payload.date,
            start_time=payload.start_time,
            duration_minutes=payload.duration_minutes,
            patient_id=payload.patient_id,
            doctor_id=payload.doctor_id,
            reason=payload.reason,
        )
    )
    return AppointmentResponse.from_result(result)


@router.put(
    "/{appointment_id}/confirmation",
    response_model=AppointmentResponse,
    summary="Confirmar una cita",
    responses={
        409: {"model": ErrorResponse, "description": "La cita no esta pendiente"},
        **_COMMON_ERRORS,
    },
)
def confirm_appointment(appointment_id: int, use_case: StatusUseCaseDep) -> AppointmentResponse:
    """Registra la confirmacion de asistencia del paciente."""
    return AppointmentResponse.from_result(use_case.confirm(appointment_id))


@router.put(
    "/{appointment_id}/completion",
    response_model=AppointmentResponse,
    summary="Marcar una cita como atendida",
    responses={
        409: {"model": ErrorResponse, "description": "La cita ya esta en un estado terminal"},
        **_COMMON_ERRORS,
    },
)
def complete_appointment(appointment_id: int, use_case: StatusUseCaseDep) -> AppointmentResponse:
    """Cierra la cita tras la consulta."""
    return AppointmentResponse.from_result(use_case.complete(appointment_id))


@router.put(
    "/{appointment_id}/cancellation",
    response_model=AppointmentResponse,
    summary="Cancelar una cita",
    description="Libera el horario del doctor y avisa al paciente.",
    responses={
        409: {"model": ErrorResponse, "description": "La cita ya fue atendida o cancelada"},
        **_COMMON_ERRORS,
    },
)
def cancel_appointment(appointment_id: int, use_case: StatusUseCaseDep) -> AppointmentResponse:
    """Cancela la cita indicada."""
    return AppointmentResponse.from_result(use_case.cancel(appointment_id))


@router.delete(
    "/{appointment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar una cita",
    description="Borrado definitivo. Para el flujo clinico habitual se prefiere la cancelacion.",
    responses={404: _COMMON_ERRORS[404]},
)
def delete_appointment(appointment_id: int, use_case: DeleteUseCaseDep) -> Response:
    """Elimina la cita del sistema."""
    use_case.execute(appointment_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
