"""Tests for the compiler module."""

import logging
import os
from pathlib import Path

import pytest
from jinja2 import Environment, UndefinedError

from astrality.compiler import (
    cast_to_numeric,
    compile_template,
    compile_template_to_string,
    jinja_environment,
)
from astrality.resolver import Resolver


@pytest.fixture
def test_templates_folder():
    return Path(__file__).parent / 'templates'


@pytest.fixture
def jinja_test_env(test_templates_folder):
    return jinja_environment(
        test_templates_folder,
        shell_command_working_directory=Path('~').resolve(),
    )


def test_rendering_environment_variables(jinja_test_env, expanded_env_dict):
    template = jinja_test_env.get_template('env_vars')
    assert template.render(env=expanded_env_dict) == \
        'test_value\nfallback_value\n'


def test_logging_undefined_variables(jinja_test_env, expanded_env_dict, caplog):
    template = jinja_test_env.get_template('env_vars')
    template.render(env=expanded_env_dict)
    assert (
        'astrality.compiler',
        logging.WARNING,
        'Template variable warning: env_UNDEFINED_VARIABLE is undefined',
    ) in caplog.record_tuples


def test_integer_indexed_templates(jinja_test_env):
    template = jinja_test_env.get_template('integer_indexed')
    context = Resolver({'section': {1: 'one', 2: 'two'}})
    assert template.render(context) == 'one\ntwo\ntwo'


def test_compilation_of_jinja_template(test_templates_folder, expanded_env_dict):
    template = test_templates_folder / 'env_vars'
    target = Path('/tmp/astrality') / template.name
    context = {'env': expanded_env_dict}
    compile_template(template, target, context, Path('/'))

    with open(target) as target:
        assert target.read() == 'test_value\nfallback_value\n'

@pytest.mark.parametrize(('string,cast,resulting_type'), [
    ('-2', -2, int),
    ('0', 0, int),
    ('1', 1, int),
    ('1.5', 1.5, float),
    ('one', 'one', str),
])
def test_cast_to_numeric(string, cast, resulting_type):
    result = cast_to_numeric(string)
    assert result == cast
    assert isinstance(result, resulting_type)

def test_run_shell_template_filter(test_templates_folder):
    shell_template_path = test_templates_folder / 'shell_filter.template'
    compiled_shell_template_path = Path('/tmp/astrality') / shell_template_path.name
    compiled_shell_template_path.touch()

    context = {}
    compile_template(
        template=shell_template_path,
        target=compiled_shell_template_path,
        context=context,
        shell_command_working_directory=Path('/'),
    )

    with open(compiled_shell_template_path) as target:
        assert target.read() == 'quick\nanother_quick\nslow_but_allowed\n\nfallback'

    if compiled_shell_template_path.is_file():
        os.remove(compiled_shell_template_path)

def test_working_directory_of_shell_command_filter(test_templates_folder):
    shell_template_path = test_templates_folder / 'shell_filter_working_directory.template'
    compiled_shell_template_path = Path('/tmp/astrality') / shell_template_path.name
    context = {}
    compile_template(
        template=shell_template_path,
        target=compiled_shell_template_path,
        context=context,
        shell_command_working_directory=Path('/'),
    )

    with open(compiled_shell_template_path) as target:
        assert target.read() == '/'

def test_environment_variable_interpolation_by_preprocessing_conf_yaml_file():
    test_conf = Path(__file__).parent / 'test_config' / 'test.yml'
    result = compile_template_to_string(
        template=test_conf,
        context={},
    )

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
    1: primary_value'''
    assert expected_result == result


@pytest.mark.slow
def test_command_substition_by_preprocessing_yaml_file():
    test_conf = Path(__file__).parent / 'test_config' / 'commands.yml'
    result = compile_template_to_string(
        template=test_conf,
        context={},
    )

    expected_result = \
'''section1:
    key1: test
    key2: test_value
    key3: test_value
    key4: '''
    assert expected_result == result

def test_handling_of_undefined_context(tmpdir, caplog):
    template = Path(tmpdir) / 'template'
    template.write_text('{{ this.is.not.defined }}')

    with pytest.raises(UndefinedError):
        string = compile_template_to_string(
            template=template,
            context={},
        )

    assert "'this' is undefined" in caplog.record_tuples[0][2]
