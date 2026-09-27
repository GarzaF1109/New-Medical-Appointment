"""Esquemas Pydantic del recurso Citas.

Viven en la capa de presentacion: describen el contrato HTTP, no el dominio.
FastAPI los usa ademas para generar el documento OpenAPI.
"""

from __future__ import annotations

from datetime import date as Date
from datetime import time

from pydantic import BaseModel, ConfigDict, Field

from app.application.dto.appointment_dto import AppointmentResult, PagedAppointments
from app.domain.entities.appointment import (
    MAX_REASON_LENGTH,
    MIN_REASON_LENGTH,
    AppointmentStatus,
)


class ScheduleAppointmentRequest(BaseModel):
    """Cuerpo de `POST /api/v1/appointments`."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "patientId": 1,
                "doctorId": 1,
                "date": "2026-10-15",
                "startTime": "10:00:00",
                "durationMinutes": 60,
                "reason": "Dolor de cabeza persistente desde hace una semana",
            }
        }
    )

    patient_id: int = Field(alias="patientId", gt=0)
    doctor_id: int = Field(alias="doctorId", gt=0)
    date: Date
    start_time: time = Field(alias="startTime")
    duration_minutes: int = Field(alias="durationMinutes", default=60, ge=15, le=480)
    reason: str = Field(min_length=MIN_REASON_LENGTH, max_length=MAX_REASON_LENGTH)


class RescheduleAppointmentRequest(BaseModel):
    """Cuerpo de `PATCH /api/v1/appointments/{id}`.

    Todos los campos son opcionales: se modifica unicamente lo que se envia.
    """

    model_config = ConfigDict(
        json_schema_extra={"example": {"date": "2026-10-16", "startTime": "11:00:00"}}
    )

    date: Date | None = None
    start_time: time | None = Field(alias="startTime", default=None)
    duration_minutes: int | None = Field(alias="durationMinutes", default=None, ge=15, le=480)
    patient_id: int | None = Field(alias="patientId", default=None, gt=0)
    doctor_id: int | None = Field(alias="doctorId", default=None, gt=0)
    reason: str | None = Field(
        default=None, min_length=MIN_REASON_LENGTH, max_length=MAX_REASON_LENGTH
    )


class AppointmentResponse(BaseModel):
    """Representacion de una cita, con enlaces de auto-descubrimiento."""

    model_config = ConfigDict(populate_by_name=True)

    id: int
    patient_id: int = Field(serialization_alias="patientId")
    patient_name: str = Field(serialization_alias="patientName")
    doctor_id: int = Field(serialization_alias="doctorId")
    doctor_name: str = Field(serialization_alias="doctorName")
    date: Date
    start_time: time = Field(serialization_alias="startTime")
    end_time: time = Field(serialization_alias="endTime")
    duration_minutes: int = Field(serialization_alias="durationMinutes")
    reason: str
    status: int
    status_label: str = Field(serialization_alias="statusLabel")
    notification_sent: bool | None = Field(serialization_alias="notificationSent", default=None)
    links: dict[str, dict[str, str]] = Field(serialization_alias="_links")

    @classmethod
    def from_result(cls, result: AppointmentResult) -> AppointmentResponse:
        """Proyecta el resultado de un caso de uso a la respuesta HTTP."""
        appointment = result.appointment
        base = f"/api/v1/appointments/{appointment.id}"
        return cls(
            id=appointment.id,
            patient_id=appointment.patient_id,
            patient_name=result.patient_name,
            doctor_id=appointment.doctor_id,
            doctor_name=result.doctor_name,
            date=appointment.slot.date,
            start_time=appointment.slot.start_time,
            end_time=appointment.slot.end_time,
            duration_minutes=appointment.slot.duration_minutes,
            reason=appointment.reason,
            status=int(appointment.status),
            status_label=appointment.status.label,
            notification_sent=result.notification_sent,
            links={
                "self": {"href": base},
                "patient": {"href": f"/api/v1/patients/{appointment.patient_id}"},
                "doctor": {"href": f"/api/v1/doctors/{appointment.doctor_id}"},
                "cancel": {"href": f"{base}/cancellation"},
            },
        )


class AppointmentCollectionResponse(BaseModel):
    """Pagina de citas con sus metadatos de paginacion."""

    model_config = ConfigDict(populate_by_name=True)

    items: list[AppointmentResponse]
    total: int
    limit: int
    offset: int

    @classmethod
    def from_page(cls, page: PagedAppointments) -> AppointmentCollectionResponse:
        """Proyecta una pagina del caso de uso a la respuesta HTTP."""
        return cls(
            items=[AppointmentResponse.from_result(item) for item in page.items],
            total=page.total,
            limit=page.limit,
            offset=page.offset,
        )


class ErrorDetail(BaseModel):
    """Detalle de un campo invalido dentro de una respuesta de error."""

    field: str
    message: str


class ErrorResponse(BaseModel):
    """Forma canonica de todas las respuestas de error de la API."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": 409,
                "code": "CONFLICT",
                "message": "El doctor ya tiene una cita en ese horario.",
            }
        }
    )

    status: int
    code: str
    message: str
    details: list[ErrorDetail] | None = None


AppointmentStatusValues = AppointmentStatus
