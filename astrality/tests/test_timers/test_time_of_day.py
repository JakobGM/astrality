"""Tests for the time_of_day timer."""

from datetime import datetime

import pytest

from astrality.timer import TimeOfDay, WorkDay


@pytest.fixture
def default_time_of_day_timer():
    """Return a default time_of_day timer object."""
    return TimeOfDay({'type': 'time_of_day'})


def test_processing_of_time_of_day_config(default_time_of_day_timer):
    """Test that the processing of the time_of_day config is correct."""
    assert 'sunday' not in default_time_of_day_timer.workdays
    assert 'monday' in default_time_of_day_timer.workdays

    assert default_time_of_day_timer.workdays['monday'].start.tm_hour == 9
    assert default_time_of_day_timer.workdays['monday'].start.tm_min == 0

    assert default_time_of_day_timer.workdays['friday'].end.tm_hour == 17
    assert default_time_of_day_timer.workdays['friday'].end.tm_min == 0


def test_current_period_of_time_of_day_timer(default_time_of_day_timer, freezer):
    work_monday = datetime(year=2018, month=2, day=12, hour=10)
    freezer.move_to(work_monday)
    assert default_time_of_day_timer.period() == 'on'

    monday_freetime = datetime(year=2018, month=2, day=12, hour=18)
    freezer.move_to(monday_freetime)
    assert default_time_of_day_timer.period() == 'off'

    saturday = datetime(year=2018, month=2, day=17, hour=10)
    freezer.move_to(saturday)
    assert default_time_of_day_timer.period() == 'off'

def test_time_until_next_period_for_time_of_day_timer(
    default_time_of_day_timer,
    freezer,
):
    work_monday = datetime(year=2018, month=2, day=12, hour=10)
    freezer.move_to(work_monday)
    assert default_time_of_day_timer.time_until_next_period().total_seconds() == 7*60*60 + 60

    monday_freetime = datetime(year=2018, month=2, day=12, hour=18)
    freezer.move_to(monday_freetime)
    assert default_time_of_day_timer.time_until_next_period().total_seconds() == 15*60*60 + 60

    saturday = datetime(year=2018, month=2, day=17, hour=10)
    freezer.move_to(saturday)
    assert default_time_of_day_timer.time_until_next_period().total_seconds() == 47*60*60 + 60
