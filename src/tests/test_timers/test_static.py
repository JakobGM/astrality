from datetime import timedelta

from timer import Static


def test_static_periods():
    static = Static({})
    assert 'static' in static.periods


def test_static_time_until_next_period():
    default_static = Static({})
    assert default_static.time_until_next_period() == timedelta(days=36500)
