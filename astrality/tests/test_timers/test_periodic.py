from datetime import datetime, timedelta

import pytest

from astrality.timer import Periodic


@pytest.fixture
def periodic():
    return Periodic({'type': 'periodic'})


@pytest.mark.parametrize("period, is_period", [
    ('0', True),
    ('1', True),
    ('80', True),
    ('-1', False),
    ('1.2', False),
    ('night', False),
])
def test_periodic_periods(period, is_period, periodic):
    assert (period in periodic.periods) == is_period


def test_periodic_beginning_period(freezer):
    periodic = Periodic({})
    assert periodic.period() == '0'


def test_periodic_standard_timedelta(freezer):
    default_periodic = Periodic({})
    assert default_periodic.time_until_next_period().total_seconds() == 3600


def test_using_custom_periodic_timer(freezer):
    custom_periodic_config = {
        'type': 'periodic',
        'seconds': 1,
        'minutes': 2,
        'hours': 3,
        'days': 4,
    }
    custom_periodic = Periodic(custom_periodic_config)
    assert custom_periodic.time_until_next_period() == timedelta(
        seconds=1,
        minutes=2,
        hours=3,
        days=4,
    )


def test_weekday_time_until_next_period_of_periodic_timer(freezer):
    now = datetime.now()
    freezer.move_to(now)
    default_periodic = Periodic({})
    assert default_periodic.time_until_next_period().total_seconds() == 60*60

    fourty_minutes = timedelta(minutes=40)
    freezer.move_to(now + fourty_minutes)
    assert default_periodic.time_until_next_period().total_seconds() == 20*60

    freezer.move_to(now + 2 * fourty_minutes)
    assert default_periodic.time_until_next_period().total_seconds() == 40*60


def test_enumeration_of_periodic_timer_periods(freezer):
    now = datetime.now()
    freezer.move_to(now)
    default_periodic = Periodic({})
    assert default_periodic.period() == '0'

    fourty_minutes = timedelta(minutes=40)
    freezer.move_to(now + fourty_minutes)
    assert default_periodic.period() == '0'

    freezer.move_to(now + 2 * fourty_minutes)
    assert default_periodic.period() == '1'
