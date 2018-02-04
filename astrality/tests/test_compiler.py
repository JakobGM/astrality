"""Tests for the compiler module."""

import logging
from pathlib import Path

import pytest
from jinja2 import Environment

from astrality.compiler import cast_to_numeric, compile_template, jinja_environment
from astrality.resolver import Resolver


@pytest.fixture
def test_templates_folder():
    return Path(__file__).parent / 'templates'


@pytest.fixture
def jinja_test_env(test_templates_folder):
    return jinja_environment(test_templates_folder)


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


# @pytest.mark.skip
def test_compilation_of_jinja_template(test_templates_folder, expanded_env_dict):
    template = test_templates_folder / 'env_vars'
    target = Path('/tmp/astrality') / template.name
    context = {'env': expanded_env_dict}
    compile_template(template, target, context)

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
