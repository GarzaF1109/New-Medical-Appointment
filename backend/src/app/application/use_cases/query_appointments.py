"""Casos de uso de solo lectura sobre citas."""

from __future__ import annotations

from app.application.dto.appointment_dto import (
    AppointmentResult,
    ListAppointmentsQuery,
    PagedAppointments,
)
from app.domain.entities.appointment import Appointment
from app.domain.exceptions import NotFoundException
from app.domain.ports.repositories import (
    AppointmentRepository,
    DoctorRepository,
    PatientRepository,
)


class QueryAppointmentsUseCase:
    """Recupera citas individuales o paginadas, resolviendo nombres."""

    def __init__(
        self,
        *,
        appointments: AppointmentRepository,
        patients: PatientRepository,
        doctors: DoctorRepository,
    ) -> None:
        self._appointments = appointments
        self._patients = patients
        self._doctors = doctors

    def get(self, appointment_id: int) -> AppointmentResult:
        """Recupera una cita por su identificador.

        Raises:
            NotFoundException: Si la cita no existe.
        """
        appointment = self._appointments.get(appointment_id)
        if appointment is None:
            raise NotFoundException("Cita", appointment_id)
        return self._enrich([appointment])[0]

    def list(self, query: ListAppointmentsQuery) -> PagedAppointments:
        """Lista citas segun los filtros indicados.

        Resuelve los nombres en lote para evitar el problema N+1 que provocaria
        consultar paciente y doctor dentro del bucle.
        """
        appointments, total = self._appointments.list(
            doctor_id=query.doctor_id,
            patient_id=query.patient_id,
            status=query.status,
            date_from=query.date_from,
            date_to=query.date_to,
            limit=query.limit,
            offset=query.offset,
        )
        return PagedAppointments(
            items=self._enrich(appointments),
            total=total,
            limit=query.limit,
            offset=query.offset,
        )

    def _enrich(self, appointments: list[Appointment]) -> list[AppointmentResult]:
        """Adjunta los nombres de paciente y doctor a cada cita."""
        patients = {p.id: p for p in self._patients.list_all()}
        doctors = {d.id: d for d in self._doctors.list_all()}
        return [
            AppointmentResult(
                appointment=appointment,
                patient_name=(
                    patients[appointment.patient_id].full_name
                    if appointment.patient_id in patients
                    else "Desconocido"
                ),
                doctor_name=(
                    doctors[appointment.doctor_id].display_name
                    if appointment.doctor_id in doctors
                    else "Desconocido"
                ),
            )
            for appointment in appointments
        ]
