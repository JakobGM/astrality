import os

import pytest

from config import user_configuration

@pytest.fixture
def conf_path():
    this_test_file = os.path.realpath(__file__)
    return '/'.join(this_test_file.split('/')[:-3])


@pytest.fixture
def conf(conf_path):
    return user_configuration(conf_path)


def test_config_directory_name(conf):
    assert conf['config_directory'][-9:] == '/solarity'


def test_name_of_config_file(conf):
    assert conf['config_file'][-14:] == '/solarity.conf'


def test_conky_module_paths(conf, conf_path):
    conky_module_paths = conf['conky_module_paths']
    assert conky_module_paths == {
        'performance': conf_path + '/conky_themes/performance',
        'time': conf_path + '/conky_themes/time',
    }

def test_loation(conf):
    location = conf['location']
    assert str(location) == 'CityNotImportant/RegionIsNotImportantEither, tz=Europe/Oslo, lat=63.45, lon=10.42'


def test_refresh_period(conf):
    assert conf['refresh_period'] == 60


def test_wallpaper_theme(conf):
    assert conf['wallpaper_theme'] == 'default'


def test_wallpaper_paths(conf, conf_path):
    base_path = conf_path + '/wallpaper_themes/default/'
    assert conf['wallpaper_paths'] == {
        'sunrise': base_path + 'sunrise.jpg',
        'morning': base_path + 'morning.jpg',
        'afternoon': base_path + 'afternoon.jpg',
        'sunset': base_path + 'sunset.jpg',
        'night': base_path + 'night.jpg',
    }
