"""Value object: numero de licencia medica."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.domain.exceptions import InvalidInputException

_LICENSE_PATTERN = re.compile(r"^L-\d{8}-\d{4}[A-Z]$")


@dataclass(frozen=True, slots=True)
class MedicalLicense:
    """Cedula profesional con formato L-YYYYMMDD-####A.

    La regla de formato vivia antes en una cadena `regex:` dentro del
    controlador. Aqui es una invariante del dominio, verificable por una prueba
    unitaria sin levantar un servidor web.
    """

    value: str

    def __post_init__(self) -> None:
        """Valida el formato al construir el objeto."""
        if not _LICENSE_PATTERN.match(self.value):
            raise InvalidInputException(
                "El formato de licencia debe ser L-YYYYMMDD-####A (Ej: L-20260526-8845A)."
            )

    def __str__(self) -> str:
        """Devuelve la cedula tal cual."""
        return self.value
