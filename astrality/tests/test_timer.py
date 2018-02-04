import pytest

from astrality.timer import Periodic, Solar, Static, Weekday, timer_factory


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


class TestTimerFactory:
    def test_timer_factory_with_solar_confi(self, solar_config):
        assert isinstance(timer_factory(solar_config), Solar)

    def test_timer_factory_with_weekday_confi(self, weekday_config):
        assert isinstance(timer_factory(weekday_config), Weekday)

    def test_timer_factory_with_periodic_confi(self, periodic_config):
        assert isinstance(timer_factory(periodic_config), Periodic)

    def test_timer_factory_with_static_confi(self, static_config):
        assert isinstance(timer_factory(static_config), Static)


@pytest.fixture
def solar_timer(solar_config):
    return Solar(solar_config)


@pytest.fixture
def weekday_timer(weekday_config):
    return Weekday(weekday_config)


@pytest.fixture
def periodic_timer(periodic_config):
    return Periodic(periodic_config)


@pytest.fixture
def static_timer(static_config):
    return Static(static_config)


class TestTimerDefaultConfiguration:
    def test_all_options_specified_of_solar_timer(
        self,
        solar_config,
        solar_timer,
    ):
        assert solar_timer.timer_config == solar_config

    def test_replacement_of_missing_timer_config_option(
        self,
        solar_config,
    ):
        solar_config.pop('elevation')
        solar_timer = Solar(solar_config)

        assert solar_timer.timer_config != solar_config
        assert solar_timer.timer_config['longitude'] == 1
        assert solar_timer.timer_config['latitude'] == 2
        assert solar_timer.timer_config['elevation'] == 0
