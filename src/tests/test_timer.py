from datetime import datetime, timedelta

import pytest

from timer import Solar


@pytest.fixture
def solar(conf):
    return Solar(conf)

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
    period = solar.period()
    assert period == 'night'


def test_that_sunrise_is_correctly_identified(solar, after_dawn, freezer):
    freezer.move_to(after_dawn)
    period = solar.period()
    assert period == 'sunrise'


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


def test_that_night_is_correctly_identified_after_dusk(solar, after_dusk, freezer):
    freezer.move_to(after_dusk)
    period = solar.period()
    assert period == 'night'


def test_that_sunset_is_correctly_identified_before_dusk(solar, before_dusk, freezer):
    freezer.move_to(before_dusk)
    period = solar.period()
    assert period == 'sunset'


def test_loation(solar):
    location = solar.construct_astral_location()
    assert str(location) == 'CityNotImportant/RegionIsNotImportantEither, tz=UTC, lat=63.45, lon=10.42'

def test_time_left_before_new_period(solar, before_dusk, freezer):
    freezer.move_to(before_dusk)
    assert solar.time_until_next_period() == 120

def test_time_right_before_midnight(solar, freezer):
    """
    This function requires special handling when the UTC time is later than all
    solar periods within the same day, which is the case right before midnight.
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
    time_left = solar.time_until_next_period()
    assert 0 < time_left < 60 * 60 * 24
