"""Pruebas de normalizacion de numeros telefonicos."""

import pytest

from app.domain.exceptions import InvalidInputException
from app.domain.value_objects.phone_number import PhoneNumber

pytestmark = pytest.mark.unit


def test_local_mexican_number_gets_country_and_mobile_prefix():
    assert PhoneNumber.parse("8112345678").value == "5218112345678"


def test_formatting_characters_are_stripped():
    assert PhoneNumber.parse("+52 (81) 1234-5678").value == "5218112345678"


def test_mobile_prefix_is_not_duplicated():
    assert PhoneNumber.parse("5218112345678").value == "5218112345678"


def test_e164_representation_includes_the_plus_sign():
    assert PhoneNumber.parse("8112345678").to_e164() == "+5218112345678"


def test_empty_input_is_rejected():
    with pytest.raises(InvalidInputException):
        PhoneNumber.parse("   ")


def test_too_short_number_is_rejected():
    with pytest.raises(InvalidInputException):
        PhoneNumber("12345")


def test_value_object_is_immutable():
    phone = PhoneNumber.parse("8112345678")

    with pytest.raises((AttributeError, TypeError)):
        phone.value = "otro"
