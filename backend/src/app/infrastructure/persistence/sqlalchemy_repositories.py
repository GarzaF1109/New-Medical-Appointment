"""Implementaciones SQLAlchemy de los puertos de persistencia."""

from __future__ import annotations

from datetime import date as Date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.entities.appointment import Appointment, AppointmentStatus
from app.domain.entities.person import Doctor, Patient
from app.domain.ports.repositories import (
    AppointmentRepository,
    DoctorRepository,
    PatientRepository,
)
from app.infrastructure.persistence.mappers import (
    appointment_to_domain,
    appointment_to_model,
    doctor_to_domain,
    doctor_to_model,
    patient_to_domain,
    patient_to_model,
)
from app.infrastructure.persistence.models import (
    AppointmentModel,
    DoctorModel,
    PatientModel,
)


class SqlAlchemyAppointmentRepository(AppointmentRepository):
    """Persistencia de citas sobre una sesion SQLAlchemy."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, appointment_id: int) -> Appointment | None:
        model = self._session.get(AppointmentModel, appointment_id)
        return appointment_to_domain(model) if model else None

    def search(
        self,
        *,
        doctor_id: int | None = None,
        patient_id: int | None = None,
        status: AppointmentStatus | None = None,
        date_from: Date | None = None,
        date_to: Date | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Appointment], int]:
        filters = []
        if doctor_id is not None:
            filters.append(AppointmentModel.doctor_id == doctor_id)
        if patient_id is not None:
            filters.append(AppointmentModel.patient_id == patient_id)
        if status is not None:
            filters.append(AppointmentModel.status == int(status))
        if date_from is not None:
            filters.append(AppointmentModel.date >= date_from)
        if date_to is not None:
            filters.append(AppointmentModel.date <= date_to)

        total = self._session.scalar(
            select(func.count()).select_from(AppointmentModel).where(*filters)
        )
        rows = self._session.scalars(
            select(AppointmentModel)
            .where(*filters)
            .order_by(AppointmentModel.date.desc(), AppointmentModel.start_time.desc())
            .limit(limit)
            .offset(offset)
        ).all()
        return [appointment_to_domain(row) for row in rows], int(total or 0)

    def list_for_doctor_on(self, doctor_id: int, day: Date) -> list[Appointment]:
        rows = self._session.scalars(
            select(AppointmentModel).where(
                AppointmentModel.doctor_id == doctor_id,
                AppointmentModel.date == day,
                AppointmentModel.status != int(AppointmentStatus.CANCELLED),
            )
        ).all()
        return [appointment_to_domain(row) for row in rows]

    def add(self, appointment: Appointment) -> Appointment:
        model = appointment_to_model(appointment)
        self._session.add(model)
        self._session.flush()
        return appointment_to_domain(model)

    def update(self, appointment: Appointment) -> Appointment:
        model = self._session.get(AppointmentModel, appointment.id)
        if model is None:
            raise ValueError(f"La cita {appointment.id} desaparecio durante la actualizacion.")
        appointment_to_model(appointment, model)
        self._session.flush()
        return appointment_to_domain(model)

    def delete(self, appointment_id: int) -> None:
        model = self._session.get(AppointmentModel, appointment_id)
        if model is not None:
            self._session.delete(model)
            self._session.flush()


class SqlAlchemyPatientRepository(PatientRepository):
    """Persistencia de pacientes sobre una sesion SQLAlchemy."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, patient_id: int) -> Patient | None:
        model = self._session.get(PatientModel, patient_id)
        return patient_to_domain(model) if model else None

    def list_all(self) -> list[Patient]:
        rows = self._session.scalars(select(PatientModel).order_by(PatientModel.full_name)).all()
        return [patient_to_domain(row) for row in rows]

    def add(self, patient: Patient) -> Patient:
        model = patient_to_model(patient)
        self._session.add(model)
        self._session.flush()
        return patient_to_domain(model)

    def update(self, patient: Patient) -> Patient:
        model = self._session.get(PatientModel, patient.id)
        if model is None:
            raise ValueError(f"El paciente {patient.id} desaparecio durante la actualizacion.")
        patient_to_model(patient, model)
        self._session.flush()
        return patient_to_domain(model)

    def delete(self, patient_id: int) -> None:
        model = self._session.get(PatientModel, patient_id)
        if model is not None:
            self._session.delete(model)
            self._session.flush()


class SqlAlchemyDoctorRepository(DoctorRepository):
    """Persistencia de doctores sobre una sesion SQLAlchemy."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, doctor_id: int) -> Doctor | None:
        model = self._session.get(DoctorModel, doctor_id)
        return doctor_to_domain(model) if model else None

    def list_all(self) -> list[Doctor]:
        rows = self._session.scalars(select(DoctorModel).order_by(DoctorModel.full_name)).all()
        return [doctor_to_domain(row) for row in rows]

    def add(self, doctor: Doctor) -> Doctor:
        model = doctor_to_model(doctor)
        self._session.add(model)
        self._session.flush()
        return doctor_to_domain(model)

    def update(self, doctor: Doctor) -> Doctor:
        model = self._session.get(DoctorModel, doctor.id)
        if model is None:
            raise ValueError(f"El doctor {doctor.id} desaparecio durante la actualizacion.")
        doctor_to_model(doctor, model)
        self._session.flush()
        return doctor_to_domain(model)

    def delete(self, doctor_id: int) -> None:
        model = self._session.get(DoctorModel, doctor_id)
        if model is not None:
            self._session.delete(model)
            self._session.flush()
