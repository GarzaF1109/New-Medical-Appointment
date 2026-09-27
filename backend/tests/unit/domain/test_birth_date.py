"""Pruebas del value object BirthDate."""

from datetime import date

import pytest

from app.domain.exceptions import InvalidInputException
from app.domain.value_objects.birth_date import BirthDate

TODAY = date(2026, 10, 1)


def test_a_birth_date_before_1900_is_rejected():
    with pytest.raises(InvalidInputException, match="1900"):
        BirthDate(date(1899, 12, 31))


def test_the_age_counts_only_completed_years():
    assert BirthDate(date(1988, 3, 14)).age_on(TODAY) == 38


def test_a_birthday_still_to_come_this_year_subtracts_one():
    # Cumple en diciembre: al 1 de octubre aun no los ha cumplido.
    assert BirthDate(date(1988, 12, 25)).age_on(TODAY) == 37


def test_the_age_on_the_exact_birthday_counts_the_year():
    assert BirthDate(date(1988, 10, 1)).age_on(TODAY) == 38


def test_a_newborn_is_zero_years_old():
    assert BirthDate(date(2026, 9, 30)).age_on(TODAY) == 0


def test_a_future_birth_date_is_detected():
    assert BirthDate(date(2027, 1, 1)).is_in_the_future(TODAY) is True


def test_the_age_of_a_future_birth_date_cannot_be_computed():
    with pytest.raises(InvalidInputException, match="futuro"):
        BirthDate(date(2027, 1, 1)).age_on(TODAY)


def test_an_age_beyond_the_human_limit_is_implausible():
    assert BirthDate(date(1900, 1, 1)).is_implausible_on(TODAY) is True


def test_a_plausible_birth_date_passes_both_checks():
    assert BirthDate(date(1988, 3, 14)).is_implausible_on(TODAY) is False


def test_it_renders_as_iso_8601():
    assert str(BirthDate(date(1988, 3, 14))) == "1988-03-14"
