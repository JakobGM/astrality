"""Tests for the static event listener subclass."""
from datetime import timedelta

from astrality.event_listener import Static


def test_static_events():
    static = Static({})
    assert 'static' in static.events


def test_static_event_listener_until_next_event():
    default_static = Static({})
    assert default_static.time_until_next_event() == timedelta(days=36500)
