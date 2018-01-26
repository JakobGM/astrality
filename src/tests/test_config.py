from configparser import ConfigParser
from math import inf
import os
from os import path
from pathlib import Path

import pytest

from config import dict_from_config_file
from resolver import Resolver
from timer import Solar


@pytest.fixture
def dummy_config():
    test_conf = Path(Path(__file__).parent, 'test.conf')
    return Resolver(dict_from_config_file(test_conf))

class TestAllConfigFeaturesFromDummyConfig:
    def test_normal_variable(self, dummy_config):
        assert dummy_config['section1']['var1'] == 'value1'

    def test_variable_interpolation(self, dummy_config):
        assert dummy_config['section1']['var2'] == 'value1/value2'
        assert dummy_config['section2']['var3'] == 'value1'

    def test_empty_string_variable(self, dummy_config):
        assert dummy_config['section2']['empty_string_var'] == ''

    def test_non_existing_variable(self, dummy_config):
        with pytest.raises(KeyError):
            assert dummy_config['section2']['not_existing_option'] is None

    def test_environment_variable_interpolation(self, dummy_config):
        assert dummy_config['section3']['env_variable'] == 'test_value, hello'

    def test_integer_index_resolution(self, dummy_config):
        assert dummy_config['section4']['1'] == 'primary_value'
        assert dummy_config['section4']['0'] == 'primary_value'
        assert dummy_config['section4']['2'] == 'primary_value'



def test_config_directory_name(conf):
    assert str(conf['_runtime']['config_directory'])[-10:] == '/astrality'


def test_name_of_config_file(conf):
    assert '/astrality.conf' in str(conf['_runtime']['config_file'])


def test_conky_module_paths(conf, conf_path):
    conky_module_paths = conf['_runtime']['conky_module_paths']
    assert conky_module_paths == {
        'performance-1920x1080': Path(conf_path, 'conky_themes', 'performance-1920x1080'),
        'time-1920x1080': Path(conf_path, 'conky_themes', 'time-1920x1080'),
    }


def test_refresh_period(conf):
    assert conf['behaviour']['refresh_period'] == '60'


def test_wallpaper_theme(conf):
    assert conf['wallpaper']['theme'] == 'default'


def test_wallpaper_paths(conf, conf_path):
    base_path = Path(conf_path, 'wallpaper_themes', 'default/')
    assert conf['_runtime']['wallpaper_paths'] == {
        'sunrise': Path(base_path, 'sunrise.jpg'),
        'morning': Path(base_path, 'morning.jpg'),
        'afternoon': Path(base_path, 'afternoon.jpg'),
        'sunset': Path(base_path, 'sunset.jpg'),
        'night': Path(base_path, 'night.jpg'),
    }

def test_that_colors_are_correctly_imported_based_on_wallpaper_theme(conf):
    assert conf['colors'] == {
        '1': {
            'afternoon': 'FC6F42',
            'morning': '5BA276',
            'night': 'CACCFD',
            'sunrise': 'FC6F42',
            'sunset': 'FEE676',
        },
        '2': {
            'afternoon': 'DB4E38',
            'morning': '76B087',
            'night': '3F72E8',
            'sunrise': 'DB4E38',
            'sunset': '9B3A1A',
        }
    }

