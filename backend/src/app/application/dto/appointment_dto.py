"""Objetos de transferencia de la capa de aplicacion.

Son comandos y resultados puros: no heredan de Pydantic ni de SQLAlchemy, de
modo que los casos de uso permanecen independientes del framework web.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date as Date
from datetime import time

from app.domain.entities.appointment import Appointment, AppointmentStatus


@dataclass(frozen=True, slots=True)
class ScheduleAppointmentCommand:
    """Datos necesarios para agendar una cita nueva."""

    patient_id: int
    doctor_id: int
    date: Date
    start_time: time
    reason: str
    duration_minutes: int = 60


@dataclass(frozen=True, slots=True)
class RescheduleAppointmentCommand:
    """Datos necesarios para mover o reasignar una cita existente.

    Los campos opcionales en None significan "no cambiar", lo que permite
    servir tanto a PATCH parcial como al reagendado a 24 horas.
    """

    appointment_id: int
    date: Date | None = None
    start_time: time | None = None
    duration_minutes: int | None = None
    patient_id: int | None = None
    doctor_id: int | None = None
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class ListAppointmentsQuery:
    """Filtros y paginacion para el listado de citas."""

    doctor_id: int | None = None
    patient_id: int | None = None
    status: AppointmentStatus | None = None
    date_from: Date | None = None
    date_to: Date | None = None
    limit: int = 50
    offset: int = 0


@dataclass(frozen=True, slots=True)
class AppointmentResult:
    """Cita enriquecida con los nombres de paciente y doctor.

    Evita que la capa de presentacion tenga que consultar repositorios para
    armar la respuesta.
    """

    appointment: Appointment
    patient_name: str
    doctor_name: str
    notification_sent: bool | None = None


@dataclass(frozen=True, slots=True)
class PagedAppointments:
    """Pagina de resultados junto al total de coincidencias."""

    items: list[AppointmentResult]
    total: int
    limit: int
    offset: int
