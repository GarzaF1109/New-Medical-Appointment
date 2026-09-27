"""Value object: fecha de nacimiento de un paciente."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date as Date

from app.domain.exceptions import InvalidInputException

MIN_BIRTH_YEAR = 1900
MAX_HUMAN_AGE = 120


@dataclass(frozen=True, slots=True)
class BirthDate:
    """Fecha de nacimiento valida.

    Encapsula el calculo de la edad, que de otro modo acabaria repetido en cada
    pantalla que lo necesite. Como el value object es inmutable, cualquier
    instancia existente es -por construccion- una fecha plausible.

    Attributes:
        value: Dia de nacimiento.
    """

    value: Date

    def __post_init__(self) -> None:
        """Valida las invariantes que no dependen del reloj."""
        if self.value.year < MIN_BIRTH_YEAR:
            raise InvalidInputException(
                f"La fecha de nacimiento no puede ser anterior al ano {MIN_BIRTH_YEAR}."
            )

    def age_on(self, reference: Date) -> int:
        """Calcula la edad cumplida en la fecha de referencia.

        Args:
            reference: Dia respecto al cual se mide la edad. Se inyecta en lugar
                de leer el reloj del sistema para que las pruebas sean
                deterministas.

        Returns:
            Anos cumplidos, nunca negativo.

        Raises:
            InvalidInputException: Si la fecha de nacimiento es posterior a la
                referencia.
        """
        if self.is_in_the_future(reference):
            raise InvalidInputException("La fecha de nacimiento no puede estar en el futuro.")
        had_birthday = (reference.month, reference.day) >= (self.value.month, self.value.day)
        return reference.year - self.value.year - (0 if had_birthday else 1)

    def is_in_the_future(self, today: Date) -> bool:
        """Indica si la fecha aun no ha ocurrido respecto al dia dado."""
        return self.value > today

    def is_implausible_on(self, today: Date) -> bool:
        """Indica si la fecha es imposible para una persona viva.

        Cubre los dos extremos que el constructor no puede verificar por si
        solo: nacer en el futuro y superar la edad humana documentada.
        """
        if self.is_in_the_future(today):
            return True
        return self.age_on(today) > MAX_HUMAN_AGE

    def __str__(self) -> str:
        """Devuelve la fecha en formato ISO 8601."""
        return self.value.isoformat()
