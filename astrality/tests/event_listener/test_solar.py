"""Tests for the solar event listener subclass."""
from datetime import datetime, timedelta

from dateutil.tz import tzlocal
import pytest

from astrality.event_listener import Solar


@pytest.fixture
def solar_config():
    """A solar event listener configuration in Trondheim, Norway."""
    return {
        'type': 'solar',
        'latitude': 0,
        'longitude': 0,
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
    assert str(location) \
        == 'CityNotImportant/RegionIsNotImportantEither, '\
           'tz=UTC, lat=0.00, lon=0.00'


def test_time_left_before_new_event(solar, before_dusk, freezer):
    freezer.move_to(before_dusk)
    assert solar.time_until_next_event().total_seconds() == 120


def test_time_right_before_midnight(solar, freezer):
    """
    This function requires special handling when the UTC time is later than all
    solar events within the same day, which is the case right before midnight.
    """

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


@pytest.mark.parametrize(
    'hour,sun',
    [
        (23, 'night'),
        (1, 'night'),
        (5, 'sunrise'),
        (10, 'morning'),
        (13, 'afternoon'),
        (22, 'sunset'),
    ],
)
def test_locations_where_some_events_never_occur(freezer, hour, sun):
    """
    Test that locations with missing solar events are handled gracefully.

    During summer, closer to the poles, the sun never dips properly below
    the horizon. In this case astral throws an AstralError, and we have
    to fall back to some hard coded defaults instead.
    """
    summer = datetime(
        year=2018,
        month=5,
        day=24,
        hour=hour,
        minute=0,
        tzinfo=tzlocal(),
    )
    freezer.move_to(summer)

    polar_location = {
        'type': 'solar',
        'latitude': 89,
        'longitude': 89,
        'elevation': 0,
    }
    polar_sun = Solar(polar_location)
    assert polar_sun.event() == sun
    assert 0 < polar_sun.time_until_next_event().total_seconds() < 24 * 60 * 60
