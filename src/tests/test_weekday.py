from datetime import datetime, timedelta

import pytest

from timer import Weekday

@pytest.fixture
def weekday(conf):
    return Weekday(conf)

@pytest.fixture
def noon_friday():
    return datetime(year=2018, month=1, day=26, hour=12)


def test_weekday_periods(weekday):
    assert weekday.periods == (
        'monday',
        'tuesday',
        'wednesday',
        'thursday',
        'friday',
        'saturday',
        'sunday',
    )


def test_weekday_period(weekday, noon_friday, freezer):
    freezer.move_to(noon_friday)
    assert weekday.period() == 'friday'


def test_weekday_time_until_next_period(weekday, noon_friday, freezer):
    freezer.move_to(noon_friday)
    assert weekday.time_until_next_period() == timedelta(hours=12)
