"""Value object: numero telefonico en formato E.164."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.domain.exceptions import InvalidInputException
from app.domain.text_rules import validate_phone_charset

_DIGITS = re.compile(r"\D")
_MEXICO_COUNTRY_CODE = "52"
_MEXICO_MOBILE_PREFIX = "521"


@dataclass(frozen=True, slots=True)
class PhoneNumber:
    """Numero telefonico normalizado.

    Encapsula la normalizacion que en el sistema anterior vivia dispersa dentro
    del servicio de WhatsApp. Al ser un value object inmutable, cualquier
    instancia existente es -por construccion- un numero valido.

    Attributes:
        value: Digitos en formato E.164 sin el signo '+'. Ej: "5218112345678".
    """

    value: str

    def __post_init__(self) -> None:
        """Valida los digitos al construir el objeto."""
        if not self.value.isdigit():
            raise InvalidInputException("El telefono solo puede contener digitos.")
        if not 10 <= len(self.value) <= 15:
            raise InvalidInputException("El telefono debe tener entre 10 y 15 digitos.")

    @classmethod
    def parse(cls, raw: str, default_country_code: str = _MEXICO_COUNTRY_CODE) -> PhoneNumber:
        """Construye un PhoneNumber a partir de texto libre.

        Args:
            raw: Numero tal como lo captura el usuario. Puede traer espacios,
                guiones, parentesis o un prefijo '+'.
            default_country_code: Lada a anteponer si el numero viene local.

        Returns:
            Una instancia normalizada.

        Raises:
            InvalidInputException: Si el numero esta vacio o no es valido.
        """
        # Primero se comprueba el juego de caracteres: si se quitaran los
        # separadores antes, "8112345678abc" perderia las letras en silencio y
        # se guardaria como si fuera un numero valido.
        cleaned = validate_phone_charset(raw)
        digits = _DIGITS.sub("", cleaned)

        if not digits:
            raise InvalidInputException("El telefono debe contener digitos.")

        if len(digits) == 10:
            digits = default_country_code + digits

        # Mexico exige el '1' despues de la lada para lineas moviles.
        if digits.startswith(_MEXICO_COUNTRY_CODE) and not digits.startswith(_MEXICO_MOBILE_PREFIX):
            digits = _MEXICO_MOBILE_PREFIX + digits[len(_MEXICO_COUNTRY_CODE) :]

        return cls(digits)

    def to_e164(self) -> str:
        """Devuelve el numero en formato E.164 con el signo '+'."""
        return f"+{self.value}"

    def __str__(self) -> str:
        """Devuelve el numero en formato E.164."""
        return self.to_e164()
