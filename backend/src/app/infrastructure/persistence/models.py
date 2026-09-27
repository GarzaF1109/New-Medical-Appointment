"""Modelos de persistencia (SQLAlchemy).

Son estructuras de tabla, no entidades de dominio. La conversion entre ambos
mundos ocurre en `mappers.py`, de modo que un cambio de esquema no obliga a
cambiar las reglas de negocio.
"""

from __future__ import annotations

from datetime import date as Date
from datetime import datetime, time

from sqlalchemy import Date as SADate
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Time, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base declarativa compartida por todas las tablas."""


class PatientModel(Base):
    """Tabla de pacientes."""

    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    birth_date: Mapped[Date] = mapped_column(SADate, nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # La cascada la ejecuta el ORM, no la base: asi el comportamiento es el
    # mismo en SQLite -que ignora ON DELETE salvo con PRAGMA- y en PostgreSQL.
    appointments: Mapped[list[AppointmentModel]] = relationship(
        back_populates="patient", cascade="all, delete-orphan"
    )


class DoctorModel(Base):
    """Tabla de doctores."""

    __tablename__ = "doctors"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    speciality: Mapped[str] = mapped_column(String(120), nullable=False)
    medical_license_number: Mapped[str | None] = mapped_column(String(20), nullable=True)

    appointments: Mapped[list[AppointmentModel]] = relationship(
        back_populates="doctor", cascade="all, delete-orphan"
    )


class AppointmentModel(Base):
    """Tabla de citas.

    `end_time` no se almacena: es un dato derivado de `start_time` y
    `duration_minutes`, y duplicarlo abriria la puerta a inconsistencias.
    """

    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), index=True, nullable=False
    )
    doctor_id: Mapped[int] = mapped_column(
        ForeignKey("doctors.id", ondelete="CASCADE"), index=True, nullable=False
    )
    date: Mapped[Date] = mapped_column(SADate, index=True, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[int] = mapped_column(Integer, default=1, index=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    patient: Mapped[PatientModel] = relationship(back_populates="appointments")
    doctor: Mapped[DoctorModel] = relationship(back_populates="appointments")
