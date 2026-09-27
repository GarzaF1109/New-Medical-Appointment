"""Esquemas Pydantic de los catalogos de pacientes y doctores."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.domain.entities.person import Doctor, Patient


class PatientResponse(BaseModel):
    """Paciente tal como lo expone la API."""

    model_config = ConfigDict(populate_by_name=True)

    id: int
    full_name: str = Field(serialization_alias="fullName")
    phone: str | None = None

    @classmethod
    def from_entity(cls, patient: Patient) -> PatientResponse:
        """Proyecta la entidad de dominio a la respuesta HTTP."""
        return cls(
            id=patient.id,
            full_name=patient.full_name,
            phone=patient.phone.to_e164() if patient.phone else None,
        )


class DoctorResponse(BaseModel):
    """Doctor tal como lo expone la API."""

    model_config = ConfigDict(populate_by_name=True)

    id: int
    full_name: str = Field(serialization_alias="fullName")
    display_name: str = Field(serialization_alias="displayName")
    speciality: str
    medical_license_number: str | None = Field(
        serialization_alias="medicalLicenseNumber", default=None
    )

    @classmethod
    def from_entity(cls, doctor: Doctor) -> DoctorResponse:
        """Proyecta la entidad de dominio a la respuesta HTTP."""
        return cls(
            id=doctor.id,
            full_name=doctor.full_name,
            display_name=doctor.display_name,
            speciality=doctor.speciality,
            medical_license_number=str(doctor.license) if doctor.license else None,
        )
