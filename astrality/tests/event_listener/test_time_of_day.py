"""Tests for the time_of_day event listener."""

from datetime import datetime

import pytest

from astrality.event_listener import TimeOfDay, WorkDay


@pytest.fixture
def default_time_of_day_event_listener():
    """Return a default time_of_day event listener object."""
    return TimeOfDay({'type': 'time_of_day'})


def test_processing_of_time_of_day_config(default_time_of_day_event_listener):
    """Test that the processing of the time_of_day config is correct."""
    assert 'sunday' not in default_time_of_day_event_listener.workdays
    assert 'monday' in default_time_of_day_event_listener.workdays

    assert default_time_of_day_event_listener.workdays['monday'].start.tm_hour == 9
    assert default_time_of_day_event_listener.workdays['monday'].start.tm_min == 0

    assert default_time_of_day_event_listener.workdays['friday'].end.tm_hour == 17
    assert default_time_of_day_event_listener.workdays['friday'].end.tm_min == 0


def test_current_event_of_time_of_day_event_listener(
    default_time_of_day_event_listener,
    freezer,
):
    """Test that the correct events are returned."""
    work_monday = datetime(year=2018, month=2, day=12, hour=10)
    freezer.move_to(work_monday)
    assert default_time_of_day_event_listener.event() == 'on'

    monday_freetime = datetime(year=2018, month=2, day=12, hour=18)
    freezer.move_to(monday_freetime)
    assert default_time_of_day_event_listener.event() == 'off'

    saturday = datetime(year=2018, month=2, day=17, hour=10)
    freezer.move_to(saturday)
    assert default_time_of_day_event_listener.event() == 'off'

def test_time_until_next_event_for_time_of_day_event_listener(
    default_time_of_day_event_listener,
    freezer,
):
    """Test that the correct number of seconds until next period is correct."""
    work_monday = datetime(year=2018, month=2, day=12, hour=10)
    freezer.move_to(work_monday)
    assert default_time_of_day_event_listener.time_until_next_event().total_seconds() == 7*60*60 + 60

    monday_freetime = datetime(year=2018, month=2, day=12, hour=18)
    freezer.move_to(monday_freetime)
    assert default_time_of_day_event_listener.time_until_next_event().total_seconds() == 15*60*60 + 60

    saturday = datetime(year=2018, month=2, day=17, hour=10)
    freezer.move_to(saturday)
    assert default_time_of_day_event_listener.time_until_next_event().total_seconds() == 47*60*60 + 60
