"""Tests for the solar event listener subclass."""
from datetime import datetime, timedelta

import pytest

from astrality.event_listener import Solar


@pytest.fixture
def solar_config():
    """A solar event listener configuration in Trondheim, Norway."""
    return {
        'type': 'solar',
        'latitude': 63.446827,
        'longitude': 10.421906,
        'elevation': 0,
    }

@pytest.fixture
def solar(solar_config):
    """A solar event listener in Trondheim, Norway."""
    return Solar(solar_config)

# --- Times around dawn ---
@pytest.fixture
def dawn(solar):
    return solar.construct_astral_location().sun()['dawn']


@pytest.fixture
def before_dawn(dawn):
    delta = timedelta(minutes=-2)
    return dawn + delta


@pytest.fixture
def after_dawn(dawn):
    delta = timedelta(minutes=2)
    return dawn + delta


def test_that_night_is_correctly_identified(solar, before_dawn, freezer):
    freezer.move_to(before_dawn)
    event = solar.event()
    assert event == 'night'


def test_that_sunrise_is_correctly_identified(solar, after_dawn, freezer):
    freezer.move_to(after_dawn)
    event = solar.event()
    assert event == 'sunrise'


# --- Times around dusk ---
@pytest.fixture
def dusk(solar):
    return solar.construct_astral_location().sun()['dusk']


@pytest.fixture
def before_dusk(dusk):
    delta = timedelta(minutes=-2)
    return dusk + delta


@pytest.fixture
def after_dusk(dusk):
    delta = timedelta(minutes=2)
    return dusk + delta


def test_that_night_is_correctly_identified_after_dusk(
    solar,
    after_dusk,
    freezer,
):
    freezer.move_to(after_dusk)
    event = solar.event()
    assert event == 'night'


def test_that_sunset_is_correctly_identified_before_dusk(
    solar,
    before_dusk,
    freezer,
):
    freezer.move_to(before_dusk)
    event = solar.event()
    assert event == 'sunset'


def test_location(solar):
    location = solar.construct_astral_location()
    assert str(location) == 'CityNotImportant/RegionIsNotImportantEither, tz=UTC, lat=63.45, lon=10.42'

def test_time_left_before_new_event(solar, before_dusk, freezer):
    freezer.move_to(before_dusk)
    assert solar.time_until_next_event().total_seconds() == 120

def test_time_right_before_midnight(solar, freezer):
    """
    This function requires special handling when the UTC time is later than all
    solar events within the same day, which is the case right before midnight.
    """

    timezone = solar.location.timezone
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
    time_left = solar.time_until_next_event()
    assert 0 < time_left.total_seconds() < 60 * 60 * 24

def test_config_event_listener_method():
    solar_event_listener_application_config = {'type': 'solar'}
    solar_event_listener = Solar(solar_event_listener_application_config)
    assert solar_event_listener.event_listener_config['latitude'] == 0
