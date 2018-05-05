import pytest

from astrality.event_listener import (
    Periodic,
    Solar,
    Static,
    Weekday,
    event_listener_factory,
)


@pytest.fixture
def solar_config():
    return {
        'type': 'solar',
        'longitude': 1,
        'latitude': 2,
        'elevation': 3,
    }


@pytest.fixture
def weekday_config():
    return {
        'type': 'weekday',
    }


@pytest.fixture
def periodic_config():
    return {
        'type': 'periodic',
        'seconds': 0,
        'minutes': 1,
        'hours': 2,
        'days': 3,
    }


@pytest.fixture
def static_config():
    return {
        'type': 'static',
    }


class TestEventListenerFactory:
    def test_event_listener_factory_with_solar_confi(self, solar_config):
        assert isinstance(event_listener_factory(solar_config), Solar)

    def test_event_listener_factory_with_weekday_confi(self, weekday_config):
        assert isinstance(event_listener_factory(weekday_config), Weekday)

    def test_event_listener_factory_with_periodic_confi(self, periodic_config):
        assert isinstance(event_listener_factory(periodic_config), Periodic)

    def test_event_listener_factory_with_static_confi(self, static_config):
        assert isinstance(event_listener_factory(static_config), Static)


@pytest.fixture
def solar_event_listener(solar_config):
    return Solar(solar_config)


@pytest.fixture
def weekday_event_listener(weekday_config):
    return Weekday(weekday_config)


@pytest.fixture
def periodic_event_listener(periodic_config):
    return Periodic(periodic_config)


@pytest.fixture
def static_event_listener(static_config):
    return Static(static_config)


class TestEventListenerDefaultConfiguration:
    def test_all_options_specified_of_solar_event_listener(
        self,
        solar_config,
        solar_event_listener,
    ):
        assert solar_event_listener.event_listener_config == solar_config

    def test_replacement_of_missing_event_listener_config_option(
        self,
        solar_config,
    ):
        solar_config.pop('elevation')
        solar_event_listener = Solar(solar_config)

        assert solar_event_listener.event_listener_config != solar_config
        assert solar_event_listener.event_listener_config['longitude'] == 1
        assert solar_event_listener.event_listener_config['latitude'] == 2
        assert solar_event_listener.event_listener_config['elevation'] == 0
