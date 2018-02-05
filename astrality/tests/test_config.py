from configparser import ConfigParser
from datetime import datetime
import os
from pathlib import Path

import pytest

from astrality import compiler
from astrality.config import (
    dict_from_config_file,
    insert_environment_values,
    insert_command_substitutions,
    insert_into,
    generate_expanded_env_dict,
    preprocess_configuration_file,
)
from astrality.module import ModuleManager


@pytest.fixture
def dummy_config():
    test_conf = Path(__file__).parent / 'test.yaml'
    return dict_from_config_file(test_conf)


class TestAllConfigFeaturesFromDummyConfig:
    def test_normal_variable(self, dummy_config):
        assert dummy_config['context/section1']['var1'] == 'value1'

    def test_variable_interpolation(self, dummy_config):
        assert dummy_config['context/section1']['var2'] == 'value1/value2'
        assert dummy_config['context/section2']['var3'] == 'value1'

    def test_empty_string_variable(self, dummy_config):
        assert dummy_config['context/section2']['empty_string_var'] == ''

    def test_non_existing_variable(self, dummy_config):
        with pytest.raises(KeyError):
            assert dummy_config['context/section2']['not_existing_option'] is None

    def test_environment_variable_interpolation(self, dummy_config):
        assert dummy_config['context/section3']['env_variable'] == 'test_value, hello'


def test_config_directory_name(conf):
    assert str(conf['_runtime']['config_directory'])[-7:] == '/config'


def test_name_of_config_file(conf):
    assert '/astrality.yaml' in str(conf['_runtime']['config_file'])


@pytest.mark.slow
def test_that_colors_are_correctly_imported_based_on_wallpaper_theme(conf, freezer):
    midnight = datetime(year=2018, month=1, day=31, hour=0, minute=0)
    freezer.move_to(midnight)
    module_manager = ModuleManager(conf)
    assert 'colors' not in module_manager.application_context
    module_manager.finish_tasks()
    assert module_manager.application_context['colors'] == {1: 'CACCFD', 2: '3F72E8'}

def test_environment_variable_interpolation_by_preprocessing_conf_yaml_file():
    test_conf = Path(__file__).parent / 'test.yaml'
    result = preprocess_configuration_file(test_conf)

    expected_result = \
'''context/section1:
    var1: value1
    var2: value1/value2


context/section2:
    # Comment
    var3: value1
    empty_string_var: ''

context/section3:
    env_variable: test_value, hello

context/section4:
    1: primary_value
'''
    assert expected_result == result

@pytest.mark.slow
def test_command_substition_by_preprocessing_yaml_file():
    test_conf = Path(__file__).parent / 'commands.yaml'
    result = preprocess_configuration_file(test_conf)

    expected_result = \
'''section1:
    key1: test
    key2: test_value
    key3: test_value
    key4: 
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

    config_line = 'key=value-${EXAMPLE_ENV_VARIABLE}'
    expected = 'key=value-test_value'
    assert insert_environment_values(config_line) == expected

    # Test if several variables on the same line are all interpolated
    several_env_variables = 'key=${lower_case_key}-${EXAMPLE_ENV_VARIABLE}'
    expected = 'key=lower_case_value-test_value'
    assert insert_environment_values(several_env_variables) == expected

    # Check that case sensitiveness is correctly handled
    lower_case_key = 'something ${lower_case_key}'
    expected = 'something lower_case_value'
    assert insert_environment_values(lower_case_key) == expected

    upper_case_key = 'something ${UPPER_CASE_KEY}'
    expected = 'something UPPER_CASE_VALUE'
    assert insert_environment_values(upper_case_key) == expected

    # Check if interpolation is case sensitive when "conficts" occur
    lower_case_conficting_key = '${conflicting_key}'
    expected = 'value1'
    assert insert_environment_values(lower_case_conficting_key) == expected

    upper_case_conficting_key = '${CONFLICTING_KEY}'
    expected = 'value2'
    assert insert_environment_values(upper_case_conficting_key) == expected

def test_insert_context_section():
    context = compiler.context({'context/section1': {'key_one': 'value_one'}})
    assert context['section1']['key_one'] == 'value_one'

    test_config_file = Path(__file__).parent / 'test.yaml'
    context = insert_into(
        context=context,
        section='new_section',
        from_config_file=test_config_file,
        from_section='section2'
    )

    assert context['section1']['key_one'] == 'value_one'
    assert context['new_section']['var3'] == 'value1'

    context = insert_into(
        context=context,
        section='section3',
        from_config_file=test_config_file,
        from_section='section3'
    )
    assert context['section3']['env_variable'] == 'test_value, hello'

    context = insert_into(
        context=context,
        section='section1',
        from_config_file=test_config_file,
        from_section='section1'
    )
    assert context['section1']['var2'] == 'value1/value2'
    assert 'key_one' not in context['section1']

def test_insert_command_substitutions():
    string = 'some text: $(echo result)'
    assert insert_command_substitutions(string) == 'some text: result'
