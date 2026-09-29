"""Esquemas Pydantic de los catalogos de pacientes y doctores."""

from __future__ import annotations

from datetime import date as Date

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.entities.person import Doctor, Patient
from app.domain.exceptions import InvalidInputException
from app.domain.text_rules import (
    validate_free_text,
    validate_person_name,
    validate_phone_charset,
)

# Los validadores delegan en las reglas del dominio en lugar de repetirlas como
# expresiones regulares. Asi el usuario recibe el mensaje escrito para el
# ("El telefono no puede contener letras") y no el volcado del patron, y la
# regla sigue teniendo una sola definicion.


def _check_name(value: str | None) -> str | None:
    if value is None:
        return None
    try:
        return validate_person_name(value)
    except InvalidInputException as error:
        raise ValueError(error.message) from error


def _check_phone(value: str | None) -> str | None:
    if value is None:
        return None
    try:
        validate_phone_charset(value)
    except InvalidInputException as error:
        raise ValueError(error.message) from error
    return value


def _check_speciality(value: str | None) -> str | None:
    if value is None:
        return None
    try:
        return validate_free_text(value, field="La especialidad", min_len=3, max_len=120)
    except InvalidInputException as error:
        raise ValueError(error.message) from error


class PatientCreateRequest(BaseModel):
    """Alta de un paciente.

    Las cotas de longitud y el juego de caracteres los impone el dominio a
    traves de los validadores: asi el mensaje llega en espanol y la regla tiene
    una sola definicion.
    """

    model_config = ConfigDict(populate_by_name=True)

    full_name: str = Field(
        alias="fullName", description="Solo letras, espacios, guiones y apostrofes."
    )
    birth_date: Date = Field(alias="birthDate", description="Formato ISO 8601 (YYYY-MM-DD).")
    phone: str | None = Field(
        default=None,
        max_length=20,
        description="Digitos y separadores + ( ) - . y espacio. Sin letras.",
    )

    _validate_name = field_validator("full_name")(_check_name)
    _validate_phone = field_validator("phone")(_check_phone)


class PatientUpdateRequest(BaseModel):
    """Edicion parcial de un paciente.

    Un campo ausente se conserva. Para borrar el telefono hay que enviarlo
    explicitamente como `null`, distincion que `model_fields_set` permite hacer.
    """

    model_config = ConfigDict(populate_by_name=True)

    full_name: str | None = Field(default=None, alias="fullName")
    birth_date: Date | None = Field(default=None, alias="birthDate")
    phone: str | None = Field(default=None, max_length=20)

    _validate_name = field_validator("full_name")(_check_name)
    _validate_phone = field_validator("phone")(_check_phone)

    @property
    def clears_phone(self) -> bool:
        """True si la peticion pide dejar al paciente sin telefono."""
        return "phone" in self.model_fields_set and self.phone is None


class DoctorCreateRequest(BaseModel):
    """Alta de un doctor."""

    model_config = ConfigDict(populate_by_name=True)

    full_name: str = Field(alias="fullName")
    speciality: str = Field(description="Ej: Cardiologia, Medicina Interna.")
    medical_license_number: str | None = Field(
        default=None,
        alias="medicalLicenseNumber",
        max_length=20,
        description="Formato L-YYYYMMDD-####A.",
    )

    _validate_name = field_validator("full_name")(_check_name)
    _validate_speciality = field_validator("speciality")(_check_speciality)


class DoctorUpdateRequest(BaseModel):
    """Edicion parcial de un doctor."""

    model_config = ConfigDict(populate_by_name=True)

    full_name: str | None = Field(default=None, alias="fullName")
    speciality: str | None = Field(default=None)
    medical_license_number: str | None = Field(
        default=None, alias="medicalLicenseNumber", max_length=20
    )

    _validate_name = field_validator("full_name")(_check_name)
    _validate_speciality = field_validator("speciality")(_check_speciality)

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
