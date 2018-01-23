from configparser import ConfigParser
from math import inf
import os
from os import path
from pathlib import Path

import pytest

from resolver import Resolver
from timer import Solar


def test_config_directory_name(conf):
    assert conf['config_directory'][-9:] == '/solarity'


def test_name_of_config_file(conf):
    assert '/solarity.conf' in conf['config_file']


def test_conky_module_paths(conf, conf_path):
    conky_module_paths = conf['conky_module_paths']
    assert conky_module_paths == {
        'performance-1920x1080': conf_path + '/conky_themes/performance-1920x1080',
        'time-1920x1080': conf_path + '/conky_themes/time-1920x1080',
    }


def test_refresh_period(conf):
    assert conf['behaviour']['refresh_period'] == '60'


def test_wallpaper_theme(conf):
    assert conf['wallpaper']['theme'] == 'default'


def test_wallpaper_paths(conf, conf_path):
    base_path = conf_path + '/wallpaper_themes/default/'
    assert conf['wallpaper_paths'] == {
        'sunrise': base_path + 'sunrise',
        'morning': base_path + 'morning',
        'afternoon': base_path + 'afternoon',
        'sunset': base_path + 'sunset',
        'night': base_path + 'night',
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

