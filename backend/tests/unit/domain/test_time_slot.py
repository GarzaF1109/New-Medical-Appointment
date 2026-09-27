"""Pruebas de la franja horaria: aritmetica y regla de solapamiento."""

from datetime import date, datetime, time

import pytest

from app.domain.exceptions import InvalidInputException
from app.domain.value_objects.time_slot import TimeSlot

pytestmark = pytest.mark.unit

DAY = date(2026, 10, 15)


def slot(hour: int, minute: int = 0, duration: int = 60) -> TimeSlot:
    return TimeSlot(date=DAY, start_time=time(hour, minute), duration_minutes=duration)


def test_end_time_is_derived_from_start_and_duration():
    # Arrange & Act
    result = slot(10, 30, duration=45).end_time

    # Assert
    assert result == time(11, 15)


def test_rejects_duration_below_the_minimum():
    with pytest.raises(InvalidInputException):
        slot(10, duration=10)


def test_rejects_duration_above_the_maximum():
    with pytest.raises(InvalidInputException):
        slot(10, duration=500)


def test_rejects_a_slot_that_spills_into_the_next_day():
    with pytest.raises(InvalidInputException):
        slot(23, 30, duration=60)


def test_overlapping_slots_are_detected():
    assert slot(10).overlaps(slot(10, 30)) is True


def test_adjacent_slots_do_not_overlap():
    # Un intervalo semiabierto permite encadenar citas sin hueco: 10:00-11:00
    # y 11:00-12:00 conviven.
    assert slot(10).overlaps(slot(11)) is False


def test_slots_on_different_days_never_overlap():
    other = TimeSlot(date=date(2026, 10, 16), start_time=time(10, 0))

    assert slot(10).overlaps(other) is False


def test_a_slot_that_started_is_in_the_past():
    assert slot(10).is_in_the_past(datetime(2026, 10, 15, 10, 30)) is True


def test_a_future_slot_is_not_in_the_past():
    assert slot(10).is_in_the_past(datetime(2026, 10, 15, 9, 0)) is False
