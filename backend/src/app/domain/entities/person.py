"""Entidades de apoyo del slice de citas: Paciente y Doctor."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date as Date

from app.domain.text_rules import validate_free_text, validate_person_name
from app.domain.value_objects.birth_date import BirthDate
from app.domain.value_objects.medical_license import MedicalLicense
from app.domain.value_objects.phone_number import PhoneNumber

MIN_NAME_LENGTH = 3
MAX_NAME_LENGTH = 255
MIN_SPECIALITY_LENGTH = 3
MAX_SPECIALITY_LENGTH = 120


def _validate_full_name(full_name: str) -> str:
    """Normaliza y valida un nombre completo.

    Raises:
        InvalidInputException: Si esta vacio, fuera de rango, o trae numeros o
            simbolos que no aparecen en un nombre de persona.
    """
    return validate_person_name(
        full_name, field="El nombre", min_len=MIN_NAME_LENGTH, max_len=MAX_NAME_LENGTH
    )


@dataclass(frozen=True, slots=True)
class Patient:
    """Paciente que recibe atencion medica.

    Attributes:
        id: Identificador persistido. None si aun no se ha guardado.
        full_name: Nombre completo.
        birth_date: Fecha de nacimiento.
        phone: Telefono de contacto. None si no se registro, en cuyo caso el
            sistema no podra notificarle.
    """

    id: int | None
    full_name: str
    birth_date: BirthDate
    phone: PhoneNumber | None = None

    def __post_init__(self) -> None:
        """Valida el nombre al construir la entidad."""
        object.__setattr__(self, "full_name", _validate_full_name(self.full_name))

    @property
    def is_reachable(self) -> bool:
        """Indica si el paciente puede recibir notificaciones."""
        return self.phone is not None

    def age_on(self, reference: Date) -> int:
        """Edad cumplida del paciente en la fecha de referencia."""
        return self.birth_date.age_on(reference)

    def with_changes(
        self,
        *,
        full_name: str | None = None,
        birth_date: BirthDate | None = None,
        phone: PhoneNumber | None = None,
        clear_phone: bool = False,
    ) -> Patient:
        """Devuelve una copia con los campos indicados modificados.

        El paciente es inmutable, asi que actualizar significa construir una
        instancia nueva: cualquier dato invalido falla aqui y jamas llega a
        existir un paciente a medio actualizar.

        Args:
            full_name: Nuevo nombre, o None para conservarlo.
            birth_date: Nueva fecha de nacimiento, o None para conservarla.
            phone: Nuevo telefono, o None para conservarlo.
            clear_phone: True para dejar al paciente sin telefono.
        """
        return Patient(
            id=self.id,
            full_name=self.full_name if full_name is None else full_name,
            birth_date=self.birth_date if birth_date is None else birth_date,
            phone=None if clear_phone else (self.phone if phone is None else phone),
        )


@dataclass(frozen=True, slots=True)
class Doctor:
    """Medico que atiende citas.

    Attributes:
        id: Identificador persistido. None si aun no se ha guardado.
        full_name: Nombre completo.
        speciality: Especialidad medica.
        license: Cedula profesional. None si aun no se ha capturado.
    """

    id: int | None
    full_name: str
    speciality: str
    license: MedicalLicense | None = None

    def __post_init__(self) -> None:
        """Valida nombre y especialidad al construir la entidad."""
        object.__setattr__(self, "full_name", _validate_full_name(self.full_name))
        object.__setattr__(self, "speciality", self._validate_speciality(self.speciality))

    @staticmethod
    def _validate_speciality(speciality: str) -> str:
        return validate_free_text(
            speciality,
            field="La especialidad",
            min_len=MIN_SPECIALITY_LENGTH,
            max_len=MAX_SPECIALITY_LENGTH,
        )

    @property
    def display_name(self) -> str:
        """Nombre con el titulo profesional antepuesto."""
        return f"Dr(a). {self.full_name}"

    def with_changes(
        self,
        *,
        full_name: str | None = None,
        speciality: str | None = None,
        license: MedicalLicense | None = None,
        clear_license: bool = False,
    ) -> Doctor:
        """Devuelve una copia con los campos indicados modificados.

        Args:
            full_name: Nuevo nombre, o None para conservarlo.
            speciality: Nueva especialidad, o None para conservarla.
            license: Nueva cedula, o None para conservarla.
            clear_license: True para dejar al doctor sin cedula registrada.
        """
        return Doctor(
            id=self.id,
            full_name=self.full_name if full_name is None else full_name,
            speciality=self.speciality if speciality is None else speciality,
            license=None if clear_license else (self.license if license is None else license),
        )
