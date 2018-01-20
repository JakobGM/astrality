from datetime import timedelta

import pytest

from time_of_day import is_new_time_of_day, period_of_day


# --- Times around dawn ---
@pytest.fixture
def dawn(conf):
    return conf['location']['astral'].sun()['dawn']


@pytest.fixture
def before_dawn(dawn):
    delta = timedelta(minutes=-2)
    return dawn + delta


@pytest.fixture
def after_dawn(dawn):
    delta = timedelta(minutes=2)
    return dawn + delta


def test_that_night_is_correctly_identified(before_dawn, conf, freezer):
    freezer.move_to(before_dawn)
    period = period_of_day(conf['location']['astral'])
    assert period == 'night'


def test_that_sunrise_is_correctly_identified(after_dawn, conf, freezer):
    freezer.move_to(after_dawn)
    period = period_of_day(conf['location']['astral'])
    assert period == 'sunrise'


@pytest.mark.freeze_time
def test_right_before_dawn(before_dawn, dawn, conf, freezer):
    freezer.move_to(before_dawn)
    changed, period = is_new_time_of_day('night', conf['location']['astral'])
    assert changed == False
    assert period == 'night'

    for period in ('sunrise', 'morning', 'afternoon', 'sunset',):
        assert is_new_time_of_day(period, conf['location']['astral'])[0] == True


@pytest.mark.freeze_time
def test_right_after_dawn(after_dawn, dawn, conf, freezer):
    freezer.move_to(after_dawn)
    changed, period = is_new_time_of_day('sunrise', conf['location']['astral'])
    assert changed == False
    assert period == 'sunrise'

    for period in ('morning', 'afternoon', 'sunset', 'night',):
        assert is_new_time_of_day(period, conf['location']['astral'])[0] == True


# --- Times around dusk ---
@pytest.fixture
def dusk(conf):
    return conf['location']['astral'].sun()['dusk']


@pytest.fixture
def before_dusk(dusk):
    delta = timedelta(minutes=-2)
    return dusk + delta


@pytest.fixture
def after_dusk(dusk):
    delta = timedelta(minutes=2)
    return dusk + delta


def test_that_night_is_correctly_identified_after_dusk(after_dusk, conf, freezer):
    freezer.move_to(after_dusk)
    period = period_of_day(conf['location']['astral'])
    assert period == 'night'


def test_that_sunset_is_correctly_identified_before_dusk(before_dusk, conf, freezer):
    freezer.move_to(before_dusk)
    period = period_of_day(conf['location']['astral'])
    assert period == 'sunset'


@pytest.mark.freeze_time
def test_right_before_dusk(before_dusk, dusk, conf, freezer):
    freezer.move_to(before_dusk)
    changed, period = is_new_time_of_day('sunset', conf['location']['astral'])
    assert changed == False
    assert period == 'sunset'

    for period in ('sunrise', 'morning', 'afternoon', 'night',):
        assert is_new_time_of_day(period, conf['location']['astral'])[0] == True


@pytest.mark.freeze_time
def test_right_after_dusk(after_dusk, dusk, conf, freezer):
    freezer.move_to(after_dusk)
    changed, period = is_new_time_of_day('night', conf['location']['astral'])
    assert changed == False
    assert period == 'night'

    for period in ('sunrise', 'morning', 'afternoon', 'sunset',):
        assert is_new_time_of_day(period, conf['location']['astral'])[0] == True
