"""Pruebas de las reglas de texto compartidas del dominio."""

import pytest

from app.domain.exceptions import InvalidInputException
from app.domain.text_rules import (
    normalize_spaces,
    validate_free_text,
    validate_person_name,
    validate_phone_charset,
)


def test_spaces_are_collapsed():
    assert normalize_spaces("  Ana   Maria   Lopez  ") == "Ana Maria Lopez"


# --- Nombres ---------------------------------------------------------------


def test_a_name_with_accents_and_enye_is_accepted():
    assert validate_person_name("José Muñoz Peña") == "José Muñoz Peña"


def test_a_name_with_apostrophe_and_hyphen_is_accepted():
    assert validate_person_name("Ana O'Brien Garcia-Lopez") == "Ana O'Brien Garcia-Lopez"


def test_a_name_with_digits_is_rejected():
    with pytest.raises(InvalidInputException, match="numeros"):
        validate_person_name("Ana123")


def test_a_name_of_only_digits_is_rejected():
    with pytest.raises(InvalidInputException, match="numeros"):
        validate_person_name("12345678")


def test_a_name_with_symbols_is_rejected():
    with pytest.raises(InvalidInputException, match="solo puede contener letras"):
        validate_person_name("!!!@@@###")


def test_an_html_tag_is_rejected_as_a_name():
    with pytest.raises(InvalidInputException):
        validate_person_name("<script>alert</script>")


def test_a_name_without_letters_is_rejected():
    with pytest.raises(InvalidInputException):
        validate_person_name(". - .")


def test_a_blank_name_is_rejected():
    with pytest.raises(InvalidInputException, match="obligatorio"):
        validate_person_name("   ")


def test_a_short_name_is_rejected():
    with pytest.raises(InvalidInputException, match="al menos 3"):
        validate_person_name("Al")


def test_a_long_name_is_rejected():
    with pytest.raises(InvalidInputException, match="no puede exceder"):
        validate_person_name("A" * 256)


# --- Texto libre -----------------------------------------------------------


def test_free_text_allows_digits_alongside_words():
    assert validate_free_text("Dosis de 500 mg", field="El motivo", min_len=3, max_len=50)


def test_free_text_without_letters_is_rejected():
    with pytest.raises(InvalidInputException, match="palabras"):
        validate_free_text("1234567890", field="El motivo", min_len=3, max_len=50)


def test_free_text_of_only_symbols_is_rejected():
    with pytest.raises(InvalidInputException, match="palabras"):
        validate_free_text("!!!!!!!!!!", field="El motivo", min_len=3, max_len=50)


# --- Telefono --------------------------------------------------------------


def test_human_separators_are_allowed_in_a_phone():
    assert validate_phone_charset("(81) 1234-5678") == "(81) 1234-5678"


def test_letters_next_to_valid_digits_are_rejected():
    # Antes se borraban en silencio y el numero se guardaba como valido.
    with pytest.raises(InvalidInputException, match="letras"):
        validate_phone_charset("8112345678abc")


def test_leading_letters_are_rejected():
    with pytest.raises(InvalidInputException, match="letras"):
        validate_phone_charset("abc8112345678")


def test_exclamation_marks_are_rejected_in_a_phone():
    with pytest.raises(InvalidInputException, match="separadores"):
        validate_phone_charset("8112345678!!!")


def test_a_blank_phone_is_rejected():
    with pytest.raises(InvalidInputException, match="obligatorio"):
        validate_phone_charset("  ")
