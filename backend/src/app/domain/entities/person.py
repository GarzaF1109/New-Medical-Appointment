"""Entidades de apoyo del slice de citas: Paciente y Doctor."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.value_objects.medical_license import MedicalLicense
from app.domain.value_objects.phone_number import PhoneNumber


@dataclass(frozen=True, slots=True)
class Patient:
    """Paciente que recibe atencion medica.

    Attributes:
        id: Identificador persistido.
        full_name: Nombre completo.
        phone: Telefono de contacto. None si no se registro, en cuyo caso el
            sistema no podra notificarle.
    """

    id: int
    full_name: str
    phone: PhoneNumber | None = None

    @property
    def is_reachable(self) -> bool:
        """Indica si el paciente puede recibir notificaciones."""
        return self.phone is not None


@dataclass(frozen=True, slots=True)
class Doctor:
    """Medico que atiende citas.

    Attributes:
        id: Identificador persistido.
        full_name: Nombre completo.
        speciality: Especialidad medica.
        license: Cedula profesional. None si aun no se ha capturado.
    """

    id: int
    full_name: str
    speciality: str
    license: MedicalLicense | None = None

    @property
    def display_name(self) -> str:
        """Nombre con el titulo profesional antepuesto."""
        return f"Dr(a). {self.full_name}"
