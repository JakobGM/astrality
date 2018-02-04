from datetime import datetime, timedelta
import logging

import pytest

from astrality.timer import Weekday

@pytest.fixture
def weekday():
    return Weekday({'type': 'weekday'})

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


def test_using_force_period_config_option(noon_friday, freezer, caplog):
    solar_timer_application_config = {
        'type': 'weekday',
        'force_period': 'monday',
    }
    freezer.move_to(noon_friday)
    weekday_timer = Weekday(solar_timer_application_config)

    # Even though it is friday, the force option makes the timer return 'monday'
    # as the current period.
    assert weekday_timer.period() == 'monday'

    # And there are no errors logged, since 'monday' is a valid Weekday period
    assert len(caplog.record_tuples) == 0


def test_using_force_period_config_option_with_wrong_period_type(
    noon_friday,
    freezer,
    caplog,
):
    solar_timer_application_config = {
        'type': 'weekday',
        'force_period': 'Mothers_day',
    }
    freezer.move_to(noon_friday)
    weekday_timer = Weekday(solar_timer_application_config)

    # Even though it is friday, the force option makes the timer return
    # 'Mothers_day' as the current period.
    assert weekday_timer.period() == 'Mothers_day'

    # There is a warnig for using an invalid weekday period
    assert logging.WARNING == caplog.record_tuples[0][1]
