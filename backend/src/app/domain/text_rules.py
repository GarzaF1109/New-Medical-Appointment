"""Reglas de validacion de texto compartidas por el dominio.

Viven aqui -y no en los esquemas de la API- porque son invariantes del negocio:
un paciente con nombre "12345" es invalido venga de HTTP, de una siembra o de
una importacion masiva. La capa de presentacion las repite como `pattern` de
Pydantic solo para poder senalar el campo culpable al usuario.
"""

from __future__ import annotations

import re

from app.domain.exceptions import InvalidInputException

# Letras con acentos y ñ, espacios y los signos que aparecen en nombres reales
# (O'Brien, Garcia-Lopez, Ma. Elena). Deliberadamente sin digitos.
_NAME_ALLOWED = re.compile(r"^[A-Za-zÁÉÍÓÚáéíóúÑñÜü' .\-]+$")

# Los nombres necesitan al menos una letra: " . - " no es un nombre.
_HAS_LETTER = re.compile(r"[A-Za-zÁÉÍÓÚáéíóúÑñÜü]")

# Espacios repetidos que conviene colapsar antes de guardar.
_SPACES = re.compile(r"\s+")

# En un telefono se aceptan separadores humanos, pero jamas letras.
_PHONE_ALLOWED = re.compile(r"^[+0-9 ().\-]+$")


def normalize_spaces(raw: str) -> str:
    """Recorta los extremos y colapsa espacios repetidos."""
    return _SPACES.sub(" ", (raw or "").strip())


def validate_person_name(
    raw: str, *, field: str = "El nombre", min_len: int = 3, max_len: int = 255
) -> str:
    """Valida un nombre propio y lo devuelve normalizado.

    Args:
        raw: Texto capturado por el usuario.
        field: Como nombrar el campo en el mensaje de error.
        min_len: Longitud minima tras normalizar.
        max_len: Longitud maxima tras normalizar.

    Returns:
        El nombre sin espacios sobrantes.

    Raises:
        InvalidInputException: Si esta vacio, es muy corto o largo, o contiene
            digitos o simbolos que no aparecen en un nombre.
    """
    cleaned = normalize_spaces(raw)

    if not cleaned:
        raise InvalidInputException(f"{field} es obligatorio.")
    if len(cleaned) < min_len:
        raise InvalidInputException(f"{field} debe tener al menos {min_len} caracteres.")
    if len(cleaned) > max_len:
        raise InvalidInputException(f"{field} no puede exceder {max_len} caracteres.")
    if any(character.isdigit() for character in cleaned):
        raise InvalidInputException(f"{field} no puede contener numeros.")
    if not _NAME_ALLOWED.match(cleaned):
        raise InvalidInputException(
            f"{field} solo puede contener letras, espacios, guiones y apostrofes."
        )
    if not _HAS_LETTER.search(cleaned):
        raise InvalidInputException(f"{field} debe contener al menos una letra.")
    return cleaned


def validate_free_text(
    raw: str, *, field: str, min_len: int, max_len: int, require_letters: bool = True
) -> str:
    """Valida un texto libre -motivo de consulta, especialidad- y lo normaliza.

    A diferencia de un nombre, aqui se permiten digitos y puntuacion: una
    especialidad puede ser "Medicina Interna" y un motivo puede citar una
    dosis. Lo que no se permite es un texto sin una sola letra, que es como
    pasan los "!!!!!!!!!!" y los "1234567890".

    Raises:
        InvalidInputException: Si esta vacio, fuera de rango o sin letras.
    """
    cleaned = normalize_spaces(raw)

    if not cleaned:
        raise InvalidInputException(f"{field} es obligatorio.")
    if len(cleaned) < min_len:
        raise InvalidInputException(f"{field} debe tener al menos {min_len} caracteres.")
    if len(cleaned) > max_len:
        raise InvalidInputException(f"{field} no puede exceder {max_len} caracteres.")
    if require_letters and not _HAS_LETTER.search(cleaned):
        raise InvalidInputException(f"{field} debe contener palabras, no solo numeros o simbolos.")
    return cleaned


def validate_phone_charset(raw: str) -> str:
    """Comprueba que el telefono solo traiga digitos y separadores.

    Se ejecuta **antes** de quitar los separadores. Sin esta comprobacion,
    "8112345678abc" perderia las letras en silencio y se guardaria como si el
    usuario hubiera escrito un numero correcto.

    Raises:
        InvalidInputException: Si aparece cualquier letra u otro simbolo.
    """
    cleaned = (raw or "").strip()
    if not cleaned:
        raise InvalidInputException("El telefono es obligatorio.")
    if any(character.isalpha() for character in cleaned):
        raise InvalidInputException("El telefono no puede contener letras.")
    if not _PHONE_ALLOWED.match(cleaned):
        raise InvalidInputException(
            "El telefono solo puede contener digitos y los separadores + ( ) - . y espacio."
        )
    return cleaned
