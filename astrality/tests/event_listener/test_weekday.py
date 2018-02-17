from datetime import datetime, timedelta
import logging

import pytest

from astrality.event_listener import Weekday


@pytest.fixture
def weekday():
    """Return default weekday timer."""
    return Weekday({'type': 'weekday'})


@pytest.fixture
def noon_friday():
    return datetime(year=2018, month=1, day=26, hour=12)


def test_weekday_events(weekday):
    assert weekday.events == (
        'monday',
        'tuesday',
        'wednesday',
        'thursday',
        'friday',
        'saturday',
        'sunday',
    )


def test_weekday_event(weekday, noon_friday, freezer):
    """Test that the correct weekday is identified."""

    freezer.move_to(noon_friday)
    assert weekday.event() == 'friday'


def test_weekday_time_until_next_event(weekday, noon_friday, freezer):
    """Test that the number of seconds until next weekday is correct."""

    freezer.move_to(noon_friday)
    assert weekday.time_until_next_event() == timedelta(hours=12)


def test_using_force_event_config_option(noon_friday, freezer, caplog):
    """Test the use of force_event option."""

    solar_event_listener_application_config = {
        'type': 'weekday',
        'force_event': 'monday',
    }
    freezer.move_to(noon_friday)
    weekday_event_listener = Weekday(solar_event_listener_application_config)

    # Even though it is friday, the force option makes the event listener
    # return 'monday' as the current event.
    assert weekday_event_listener.event() == 'monday'

    # And there are no errors logged, since 'monday' is a valid Weekday event
    assert len(caplog.record_tuples) == 0


def test_using_force_event_config_option_with_wrong_event_type(
    noon_friday,
    freezer,
    caplog,
):
    """Test the use of force_event with an invalid event type."""

    solar_event_listener_application_config = {
        'type': 'weekday',
        'force_event': 'Mothers_day',
    }
    freezer.move_to(noon_friday)
    weekday_event_listener = Weekday(solar_event_listener_application_config)

    # Even though it is friday, the force option makes the event listener
    # return 'Mothers_day' as the current event.
    assert weekday_event_listener.event() == 'Mothers_day'

    # There is a warnig for using an invalid weekday event
    assert logging.WARNING == caplog.record_tuples[0][1]
