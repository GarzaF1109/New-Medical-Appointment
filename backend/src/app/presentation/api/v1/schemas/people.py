"""Esquemas Pydantic de los catalogos de pacientes y doctores."""

from __future__ import annotations

from datetime import date as Date

from pydantic import BaseModel, ConfigDict, Field

from app.domain.entities.person import Doctor, Patient


class PatientCreateRequest(BaseModel):
    """Alta de un paciente."""

    model_config = ConfigDict(populate_by_name=True)

    full_name: str = Field(alias="fullName", min_length=3, max_length=255)
    birth_date: Date = Field(alias="birthDate")
    phone: str | None = Field(default=None, max_length=20)


class PatientUpdateRequest(BaseModel):
    """Edicion parcial de un paciente.

    Un campo ausente se conserva. Para borrar el telefono hay que enviarlo
    explicitamente como `null`, distincion que `model_fields_set` permite hacer.
    """

    model_config = ConfigDict(populate_by_name=True)

    full_name: str | None = Field(default=None, alias="fullName", min_length=3, max_length=255)
    birth_date: Date | None = Field(default=None, alias="birthDate")
    phone: str | None = Field(default=None, max_length=20)

    @property
    def clears_phone(self) -> bool:
        """True si la peticion pide dejar al paciente sin telefono."""
        return "phone" in self.model_fields_set and self.phone is None


class DoctorCreateRequest(BaseModel):
    """Alta de un doctor."""

    model_config = ConfigDict(populate_by_name=True)

    full_name: str = Field(alias="fullName", min_length=3, max_length=255)
    speciality: str = Field(min_length=1, max_length=120)
    medical_license_number: str | None = Field(
        default=None, alias="medicalLicenseNumber", max_length=20
    )


class DoctorUpdateRequest(BaseModel):
    """Edicion parcial de un doctor."""

    model_config = ConfigDict(populate_by_name=True)

    full_name: str | None = Field(default=None, alias="fullName", min_length=3, max_length=255)
    speciality: str | None = Field(default=None, min_length=1, max_length=120)
    medical_license_number: str | None = Field(
        default=None, alias="medicalLicenseNumber", max_length=20
    )

    @property
    def clears_license(self) -> bool:
        """True si la peticion pide dejar al doctor sin cedula registrada."""
        return "medical_license_number" in self.model_fields_set and (
            self.medical_license_number is None
        )


class PatientResponse(BaseModel):
    """Paciente tal como lo expone la API."""

    model_config = ConfigDict(populate_by_name=True)

    id: int
    full_name: str = Field(serialization_alias="fullName")
    birth_date: Date = Field(serialization_alias="birthDate")
    age: int
    phone: str | None = None

    @classmethod
    def from_entity(cls, patient: Patient, *, today: Date) -> PatientResponse:
        """Proyecta la entidad de dominio a la respuesta HTTP.

        Args:
            patient: Entidad a proyectar.
            today: Dia de referencia para calcular la edad.

        Raises:
            ValueError: Si la entidad aun no se ha persistido y no tiene ID.
        """
        if patient.id is None:
            raise ValueError("No se puede exponer un paciente sin identificador.")
        return cls(
            id=patient.id,
            full_name=patient.full_name,
            birth_date=patient.birth_date.value,
            age=patient.age_on(today),
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
        """Proyecta la entidad de dominio a la respuesta HTTP.

        Raises:
            ValueError: Si la entidad aun no se ha persistido y no tiene ID.
        """
        if doctor.id is None:
            raise ValueError("No se puede exponer un doctor sin identificador.")
        return cls(
            id=doctor.id,
            full_name=doctor.full_name,
            display_name=doctor.display_name,
            speciality=doctor.speciality,
            medical_license_number=str(doctor.license) if doctor.license else None,
        )
