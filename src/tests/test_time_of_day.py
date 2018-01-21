from datetime import timedelta

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
