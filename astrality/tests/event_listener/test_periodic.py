from datetime import datetime, timedelta

import pytest

from astrality.event_listener import Periodic


@pytest.fixture
def periodic():
    """Return a default periodic timer."""
    return Periodic({'type': 'periodic'})


@pytest.mark.parametrize("event, is_event", [
    ('0', True),
    ('1', True),
    ('80', True),
    ('-1', False),
    ('1.2', False),
    ('night', False),
])
def test_periodic_events_are_correctly_identified(event, is_event, periodic):
    """Test that events are correctly identified as valid."""
    assert (event in periodic.events) == is_event


def test_periodic_beginning_event(freezer):
    """Test that the first event is 0."""
    periodic = Periodic({})
    assert periodic.event() == '0'


def test_periodic_standard_timedelta(freezer):
    """Test that the maximum timedelta is returned."""
    default_periodic = Periodic({})
    assert default_periodic.time_until_next_event().total_seconds() == 3600


def test_using_custom_periodic_event_listener(freezer):
    """Test that a custom defined period is correctly behaved."""
    custom_periodic_config = {
        'type': 'periodic',
        'seconds': 1,
        'minutes': 2,
        'hours': 3,
        'days': 4,
    }
    custom_periodic = Periodic(custom_periodic_config)
    assert custom_periodic.time_until_next_event() == timedelta(
        seconds=1,
        minutes=2,
        hours=3,
        days=4,
    )


def test_weekday_time_until_next_event_of_periodic_event_listener(freezer):
    """Test that time left until next event is always correct."""
    now = datetime.now()
    freezer.move_to(now)
    default_periodic = Periodic({})
    assert default_periodic.time_until_next_event().total_seconds() == 60*60

    fourty_minutes = timedelta(minutes=40)
    freezer.move_to(now + fourty_minutes)
    assert default_periodic.time_until_next_event().total_seconds() == 20*60

    freezer.move_to(now + 2 * fourty_minutes)
    assert default_periodic.time_until_next_event().total_seconds() == 40*60


def test_enumeration_of_periodic_event_listener_events(freezer):
    """Test that event is incremented by one correctly."""
    now = datetime.now()
    freezer.move_to(now)
    default_periodic = Periodic({})
    assert default_periodic.event() == '0'

    fourty_minutes = timedelta(minutes=40)
    freezer.move_to(now + fourty_minutes)
    assert default_periodic.event() == '0'

    freezer.move_to(now + 2 * fourty_minutes)
    assert default_periodic.event() == '1'
