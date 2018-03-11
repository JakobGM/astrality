"""Tests for the daylight event listener subclass."""
from datetime import datetime, timedelta

import pytest

from astrality.event_listener import Daylight


@pytest.fixture
def daylight_config():
    """A daylight event listener configuration in Trondheim, Norway."""
    return {
        'type': 'daylight',
        'latitude': 63.446827,
        'longitude': 10.421906,
        'elevation': 0,
    }

@pytest.fixture
def daylight(daylight_config):
    """A daylight event listener in Trondheim, Norway."""
    return Daylight(daylight_config)

# --- Times around dawn ---
@pytest.fixture
def dawn(daylight):
    return daylight.construct_astral_location().sun()['dawn']


@pytest.fixture
def before_dawn(dawn):
    delta = timedelta(minutes=-2)
    return dawn + delta


@pytest.fixture
def after_dawn(dawn):
    delta = timedelta(minutes=2)
    return dawn + delta


def test_that_night_is_correctly_identified(daylight, before_dawn, freezer):
    freezer.move_to(before_dawn)
    event = daylight.event()
    assert event == 'night'


def test_that_day_is_correctly_identified(daylight, after_dawn, freezer):
    freezer.move_to(after_dawn)
    event = daylight.event()
    assert event == 'day'


# --- Times around dusk ---
@pytest.fixture
def dusk(daylight):
    return daylight.construct_astral_location().sun()['dusk']


@pytest.fixture
def before_dusk(dusk):
    delta = timedelta(minutes=-2)
    return dusk + delta


@pytest.fixture
def after_dusk(dusk):
    delta = timedelta(minutes=2)
    return dusk + delta


def test_that_night_is_correctly_identified_after_dusk(
    daylight,
    after_dusk,
    freezer,
):
    freezer.move_to(after_dusk)
    event = daylight.event()
    assert event == 'night'


def test_that_day_is_correctly_identified_before_dusk(
    daylight,
    before_dusk,
    freezer,
):
    freezer.move_to(before_dusk)
    event = daylight.event()
    assert event == 'day'


def test_time_left_before_new_event(daylight, before_dusk, freezer):
    freezer.move_to(before_dusk)
    assert daylight.time_until_next_event().total_seconds() == 120


def test_time_right_before_midnight(daylight, freezer):
    """
    This function requires special handling when the UTC time is later than all
    daylight events within the same day, which is the case right before midnight.
    """

    timezone = daylight.location.timezone
    before_midnight = datetime(
        year=2019,
        month=12,
        day=23,
        hour=23,
        second=59,
        microsecond=0,
    )
    freezer.move_to(before_midnight)

    # Test that the time left is within the bounds of 0 to 24 hours
    time_left = daylight.time_until_next_event()
    assert 0 < time_left.total_seconds() < 60 * 60 * 24

def test_time_until_night_when_other_periods_are_inbetween(daylight, before_dusk, freezer):
    freezer.move_to(before_dusk - timedelta(hours=6))
    assert daylight.time_until_next_event().total_seconds() == 120 + 6*60*60
