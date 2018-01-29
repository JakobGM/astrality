from configparser import ConfigParser
from math import inf
import os
from os import path
from pathlib import Path

import pytest

from config import (
    dict_from_config_file,
    insert_environment_values,
    generate_expanded_env_dict,
    preprocess_environment_variables,
)
from resolver import Resolver


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

def test_environment_variable_interpolation_by_preprocessing_conf_ini_file():
    test_conf = Path(__file__).parent / 'test.conf'
    result = preprocess_environment_variables(test_conf)

    expected_result = \
'''[section1]
var1 = value1
var2 = ${var1}/value2


[section2]
# Comment
var3 = ${section1:var1}
empty_string_var =

[section3]
env_variable = test_value, hello

[section4]
1 = primary_value
'''
    assert expected_result == result

def test_generation_of_expanded_env_dict():
    env_dict = generate_expanded_env_dict()
    assert len(env_dict) == len(os.environ)

    for name, value in os.environ.items():
        if not '$' in value:
            assert env_dict[name] == value

def test_insert_environment_variables():
    '''Pytest sets the following environment variables
        EXAMPLE_ENV_VARIABLE=test_value
        lower_case_key=lower_case_value
        UPPER_CASE_KEY=UPPER_CASE_VALUE
        conflicting_key=value1
        CONFLICTING_KEY=value2
    '''

    config_line = 'key=value-${env:EXAMPLE_ENV_VARIABLE}'
    expected = 'key=value-test_value'
    assert insert_environment_values(config_line) == expected

    # Test if several variables on the same line are all interpolated
    several_env_variables = 'key=${env:lower_case_key}-${env:EXAMPLE_ENV_VARIABLE}'
    expected = 'key=lower_case_value-test_value'
    assert insert_environment_values(several_env_variables) == expected

    # Check that case sensitiveness is correctly handled
    lower_case_key = 'something ${env:lower_case_key}'
    expected = 'something lower_case_value'
    assert insert_environment_values(lower_case_key) == expected

    upper_case_key = 'something ${env:UPPER_CASE_KEY}'
    expected = 'something UPPER_CASE_VALUE'
    assert insert_environment_values(upper_case_key) == expected

    # Check if interpolation is case sensitive when "conficts" occur
    lower_case_conficting_key = '${env:conflicting_key}'
    expected = 'value1'
    assert insert_environment_values(lower_case_conficting_key) == expected

    upper_case_conficting_key = '${env:CONFLICTING_KEY}'
    expected = 'value2'
    assert insert_environment_values(upper_case_conficting_key) == expected
