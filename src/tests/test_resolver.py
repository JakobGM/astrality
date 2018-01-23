from configparser import ConfigParser
from math import inf
from os import path
import os
from pathlib import Path

import pytest

from resolver import Resolver
from timer import Solar


@pytest.fixture
def solarity_conf_file_dict(conf):
    config_directory = Path(__file__).parents[2]
    return {
        'DEFAULT': {},
        'behaviour': {'refresh_period': '60'},
        'conky': {'modules': 'performance-1920x1080 time-1920x1080',
                  'startup_delay': '0'},
        'fonts': {'1': 'FuraCode Nerd Font'},
        'location': {
            'elevation': '0',
            'latitude': '63.446827',
            'longitude': '10.421906',
        },
        'timer': {'type': 'solar'},
        'wallpaper': {'feh_option': '--bg-fill', 'theme': 'default'},
    }

@pytest.fixture
def wallpaper_conf_file_dict(conf):
    config_directory = Path(__file__).parents[2]
    return {
        'colors': {'1': {'afternoon': 'FC6F42',
                         'morning': '5BA276',
                         'night': 'CACCFD',
                         'sunrise': 'FC6F42',
                         'sunset': 'FEE676'},
                   '2': {'afternoon': 'DB4E38',
                         'morning': '76B087',
                         'night': '3F72E8',
                         'sunrise': 'DB4E38',
                         'sunset': '9B3A1A'}},
    }

@pytest.fixture
def infered_conf_dict(conf):
    config_directory = Path(__file__).parents[2]
    return {
        'config_directory': str(config_directory),
        'config_file': str(path.join(
            config_directory,
            'solarity.conf.example',
        )),
        'conky': {'modules': 'performance-1920x1080 time-1920x1080',
                  'startup_delay': '0'},
        'conky_module_paths': {
            'performance-1920x1080': str(path.join(
                config_directory,
                'conky_themes',
                'performance-1920x1080',
            )),
            'time-1920x1080': str(path.join(config_directory, 'conky_themes', 'time-1920x1080')),
        },
        'conky_module_templates': {
            'performance-1920x1080': str(path.join(
                config_directory,
                'conky_themes',
                'performance-1920x1080',
                'template.conf',
            )),
            'time-1920x1080': str(path.join(
                config_directory,
                'conky_themes',
                'time-1920x1080',
                'template.conf',
            ))},
        'conky_temp_files': {
            'performance-1920x1080': conf['conky_temp_files']['performance-1920x1080'],
            'time-1920x1080': conf['conky_temp_files']['time-1920x1080']},
        'fonts': {'1': 'FuraCode Nerd Font'},
        'location': {
            'elevation': '0',
            'latitude': '63.446827',
            'longitude': '10.421906',
        },
        'periods': ('sunrise', 'morning', 'afternoon', 'sunset', 'night'),
        'temp_directory': str(path.join(os.environ.get('TMPDIR', '/tmp'), 'solarity')),
        'timer': {'type': 'solar'},
        'timer_class': Solar,
        'wallpaper': {'feh_option': '--bg-fill', 'theme': 'default'},
        'wallpaper_paths': {
            'afternoon': str(path.join(
                config_directory,
                'wallpaper_themes',
                'default',
                'afternoon',
            )),
            'morning': str(path.join(
                config_directory,
                'wallpaper_themes',
                'default',
                'morning',
            )),
            'night': str(path.join(
                config_directory,
                'wallpaper_themes',
                'default',
                'night',
            )),
            'sunrise': str(path.join(
                config_directory,
                'wallpaper_themes',
                'default',
                'sunrise',
            )),
            'sunset': str(path.join(
                config_directory,
                'wallpaper_themes',
                'default',
                'sunset',
            )),
        },
        'wallpaper_theme_directory': str(path.join(
            config_directory,
            'wallpaper_themes',
            'default',
        )),
    }

@pytest.fixture
def fully_processed_conf_dict(conf):
    config_directory = Path(__file__).parents[2]
    return {
        'DEFAULT': {},
        'behaviour': {'refresh_period': '60'},
        'colors': {'1': {'afternoon': 'FC6F42',
                         'morning': '5BA276',
                         'night': 'CACCFD',
                         'sunrise': 'FC6F42',
                         'sunset': 'FEE676'},
                   '2': {'afternoon': 'DB4E38',
                         'morning': '76B087',
                         'night': '3F72E8',
                         'sunrise': 'DB4E38',
                         'sunset': '9B3A1A'}},
        'config_directory': str(config_directory),
        'config_file': str(path.join(
            config_directory,
            'solarity.conf.example',
        )),
        'conky': {'modules': 'performance-1920x1080 time-1920x1080',
                  'startup_delay': '0'},
        'conky_module_paths': {
            'performance-1920x1080': str(path.join(
                config_directory,
                'conky_themes',
                'performance-1920x1080',
            )),
            'time-1920x1080': str(path.join(config_directory, 'conky_themes', 'time-1920x1080')),
        },
        'conky_module_templates': {
            'performance-1920x1080': str(path.join(
                config_directory,
                'conky_themes',
                'performance-1920x1080',
                'template.conf',
            )),
            'time-1920x1080': str(path.join(
                config_directory,
                'conky_themes',
                'time-1920x1080',
                'template.conf',
            ))},
        'conky_temp_files': {
            'performance-1920x1080': conf['conky_temp_files']['performance-1920x1080'],
            'time-1920x1080': conf['conky_temp_files']['time-1920x1080']},
        'fonts': {'1': 'FuraCode Nerd Font'},
        'location': {
            'elevation': '0',
            'latitude': '63.446827',
            'longitude': '10.421906',
        },
        'periods': ('sunrise', 'morning', 'afternoon', 'sunset', 'night'),
        'temp_directory': str(path.join(os.environ.get('TMPDIR', '/tmp'), 'solarity')),
        'timer': {'type': 'solar'},
        'timer_class': Solar,
        'wallpaper': {'feh_option': '--bg-fill', 'theme': 'default'},
        'wallpaper_paths': {
            'afternoon': str(path.join(
                config_directory,
                'wallpaper_themes',
                'default',
                'afternoon',
            )),
            'morning': str(path.join(
                config_directory,
                'wallpaper_themes',
                'default',
                'morning',
            )),
            'night': str(path.join(
                config_directory,
                'wallpaper_themes',
                'default',
                'night',
            )),
            'sunrise': str(path.join(
                config_directory,
                'wallpaper_themes',
                'default',
                'sunrise',
            )),
            'sunset': str(path.join(
                config_directory,
                'wallpaper_themes',
                'default',
                'sunset',
            )),
        },
        'wallpaper_theme_directory': str(path.join(
            config_directory,
            'wallpaper_themes',
            'default',
        )),
    }

@pytest.fixture
def config_parser(conf_file_path):
    config_parser = ConfigParser()
    config_parser.read(conf_file_path)
    return config_parser

class TestFixtures:
    def test_config_fixture_correctnes(self, conf, fully_processed_conf_dict):
        assert conf == fully_processed_conf_dict


class TestResolverClass:
    def test_initialization_of_config_class_with_no_config_parser(self):
        Resolver()

    def test_invocation_of_class_with_config_parser(self, conf_file_path):
        config_parser = ConfigParser()
        config_parser.read(conf_file_path)
        Resolver(config_parser)

    def test_initialization_of_config_class_with_dict(self):
        conf_dict = {
            'key1': 'value1',
            'key2': 'value2',
            'key3': ('one', 'two', 'three'),
            'key4': {'key4-1': 'uno', 'key4-2': 'dos'}
        }
        config = Resolver(conf_dict)
        assert config == conf_dict

    def test_equality_operator_on_config_class(self, config_parser, solarity_conf_file_dict):
        config = Resolver(config_parser)
        assert solarity_conf_file_dict == config

    def test_right_equality_operator_on_config_class(self, config_parser, solarity_conf_file_dict):
        config = Resolver(config_parser)
        assert config == solarity_conf_file_dict

    def test_values_for_max_key_property(self):
        config = Resolver()
        assert config._max_key == -inf

        config['string_key'] = 1
        assert config._max_key == -inf

        config['2'] = 'string_value'
        assert config._max_key == 2

        config['1'] = 'string_value'
        assert config._max_key == 2

        config['3'] = 'string_value'
        assert config._max_key == 3

    def test_getting_item_from_empty_config(self):
        config = Resolver()
        with pytest.raises(KeyError) as exception:
            config['empty_config_with_no_key']
        assert exception.value.args[0] == \
            'Tried to access key from empty Resolver section'

    def test_accessing_existing_key(self):
        config = Resolver()
        config['some_key'] = 'some_value'
        assert config['some_key'] == 'some_value'

        config['-2'] = 'some_other_value'
        assert config['-2'] == 'some_other_value'

    def test_integer_index_resolution(self):
        config = Resolver()
        config['some_key'] = 'some_value'
        config['1'] = 'FureCode Nerd Font'
        assert config['2'] == 'FureCode Nerd Font'

    def test_integer_index_resolution_without_earlier_index_key(self):
        config = Resolver()
        config['some_key'] = 'some_value'
        with pytest.raises(KeyError) as exception:
            config['2']
        assert exception.value.args[0] == \
            'Integer index "2" is non-existent and ' \
            'had no lower index to be substituted for'

    def test_index_resolution_with_string_key(self):
        config = Resolver()
        config['2'] = 'some_value'
        with pytest.raises(KeyError) as exception:
            config['test']
        assert exception.value.args[0] == 'test'

    def test_use_of_recursive_config_objects_created_by_dicts(self):
        conf_dict = {
            'key1': 'value1',
            '1': 'value2',
            '2': {'1': 'some_value'},
            'key3': ('one', 'two', 'three'),
            'key4': {'1': 'uno', 'key4-2': 'dos'}
        }
        config = Resolver(conf_dict)
        assert config == conf_dict
        assert config['3']['2'] == 'some_value'
        assert config['2'] == {'1': 'some_value'}
        assert config['3'] == {'1': 'some_value'}

        assert isinstance(config['key4'], Resolver)
        assert config['key4'] == {'1': 'uno', 'key4-2': 'dos'}
        assert config['key4']['1'] == 'uno'
        assert config['key4']['2'] == 'uno'

    def test_use_of_recursive_config_objects_created_by_config_file(self, conf_file_path):
        config_parser = ConfigParser()
        config_parser.read(conf_file_path)
        config = Resolver(config_parser)
        assert config['fonts']['1'] == 'FuraCode Nerd Font'
        assert config['fonts']['2'] == 'FuraCode Nerd Font'

    def test_getter(self):
        config = Resolver()
        assert config.get('from_empty_config') is None

        config['test'] = 'something'
        assert config.get('test') == 'something'
        assert config.get('test', '4') == 'something'

        assert config.get('non_existent_key') is None
        assert config.get('non_existent_key', '4') == '4'

    def test_items(self):
        config = Resolver()
        config['4'] = 'test'
        config['font'] = 'Comic Sans'
        config[5] = 8
        assert list(config.items()) == [('4', 'test',), ('font', 'Comic Sans',), (5, 8,)]

    def test_keys(self):
        config = Resolver()
        config['4'] = 'test'
        config['font'] = 'Comic Sans'
        config[5] = 8
        assert list(config.keys()) == ['4', 'font', 5]

    def test_values(self):
        config = Resolver()
        config['4'] = 'test'
        config['font'] = 'Comic Sans'
        config[5] = 8
        assert list(config.values()) == ['test', 'Comic Sans', 8]

    def test_update(self):
        one_conf_dict = {
            'key1': 'value1',
            '1': 'value2',
            '2': {'1': 'some_value'},
        }
        another_conf_dict = {
            'key3': ('one', 'two', 'three'),
            'key4': {'1': 'uno', 'key4-2': 'dos'}
        }
        merged_conf_dicts = {
            'key1': 'value1',
            '1': 'value2',
            '2': {'1': 'some_value'},
            'key3': ('one', 'two', 'three'),
            'key4': {'1': 'uno', 'key4-2': 'dos'}
        }
        config = Resolver(one_conf_dict)
        config.update(another_conf_dict)
        assert config == merged_conf_dicts

    def test_update_with_config_parser(self, solarity_conf_file_dict, conf_file_path):
        config_parser = ConfigParser()
        config_parser.read(conf_file_path)

        conf_dict = {'1': 'one', '2': {'uno': 'ein', 'dos': 'zwei'}}
        config = Resolver(conf_dict)
        config.update(config_parser)

        solarity_conf_file_dict.update(conf_dict)
        assert config == solarity_conf_file_dict

    @pytest.mark.skip()
    def test_use_of_replacement_resolver(conf):
        replacements = generate_replacements(conf, 'night')
        replace = generate_replacer(replacements, 'night', conf)
        assert replace('${solarity:colors:2}') == 'CACCFD'

    @pytest.mark.skip()
    def test_resolver_class():
        resolver = Resolver()
        resolver['1'] = 'firs_value'
        resolver['2'] = 'second_value'
        resolver['string_key'] = 'string_value'

        assert resolver['1'] == 'firs_value'
        assert resolver['2'] == 'second_value'
        assert resolver['3'] == 'second_value'
        assert resolver['string_key'] == 'string_value'

    @pytest.mark.skip()
    def test_resolver_class():
        resolver = Resolver()
        resolver['1'] = 'FuraCode Nerd Font'

        assert resolver['1'] == 'FuraCode Nerd Font'
