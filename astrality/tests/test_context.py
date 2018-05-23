"""Tests for Context class."""
from math import inf
from pathlib import Path
import shutil

import pytest

from astrality.context import Context


class TestContextClass:
    def test_initialization_of_config_class_with_no_config_parser(self):
        Context()

    def test_invocation_of_class_with_application_config(self, conf):
        Context(conf)

    def test_initialization_of_config_class_with_dict(self):
        conf_dict = {
            'key1': 'value1',
            'key2': 'value2',
            'key3': ('one', 'two', 'three'),
            'key4': {'key4-1': 'uno', 'key4-2': 'dos'},
        }
        config = Context(conf_dict)
        assert config == conf_dict

    def test_values_for_max_key_property(self):
        config = Context()
        assert config._max_key == -inf

        config['string_key'] = 1
        assert config._max_key == -inf

        config[2] = 'string_value'
        assert config._max_key == 2

        config[1] = 'string_value'
        assert config._max_key == 2

        config[3] = 'string_value'
        assert config._max_key == 3

    def test_getting_item_from_empty_config(self):
        config = Context()
        with pytest.raises(KeyError):
            config['empty_config_with_no_key']

    def test_accessing_existing_key(self):
        config = Context()
        config['some_key'] = 'some_value'
        assert config['some_key'] == 'some_value'

        config[-2] = 'some_other_value'
        assert config[-2] == 'some_other_value'

    def test_integer_index_resolution(self):
        config = Context()
        config['some_key'] = 'some_value'
        config[1] = 'FureCode Nerd Font'
        assert config[2] == 'FureCode Nerd Font'

    def test_integer_index_resolution_without_earlier_index_key(self):
        config = Context()
        config['some_key'] = 'some_value'
        with pytest.raises(KeyError) as exception:
            config[2]
        assert exception.value.args[0] == \
            'Integer index "2" is non-existent and ' \
            'had no lower index to be substituted for'

    def test_index_resolution_with_string_key(self):
        config = Context()
        config[2] = 'some_value'
        with pytest.raises(KeyError) as exception:
            config['test']
        assert exception.value.args[0] == 'test'

    def test_use_of_recursive_config_objects_created_by_dicts(self):
        conf_dict = {
            'key1': 'value1',
            1: 'value2',
            2: {1: 'some_value'},
            'key3': ('one', 'two', 'three'),
            'key4': {1: 'uno', 'key4-2': 'dos'},
        }
        config = Context(conf_dict)
        assert config == conf_dict
        assert config[3][2] == 'some_value'
        assert config[2] == {1: 'some_value'}
        assert config[3] == {1: 'some_value'}

        assert isinstance(config['key4'], Context)
        assert config['key4'] == {1: 'uno', 'key4-2': 'dos'}
        assert config['key4'][1] == 'uno'
        assert config['key4'][2] == 'uno'

    def test_getter(self):
        config = Context()
        assert config.get('from_empty_config') is None

        config['test'] = 'something'
        assert config.get('test') == 'something'
        assert config.get('test', '4') == 'something'

        assert config.get('non_existent_key') is None
        assert config.get('non_existent_key', '4') == '4'

    def test_items(self):
        config = Context()
        config['4'] = 'test'
        config['font'] = 'Comic Sans'
        config['5'] = '8'
        assert list(config.items()) == [
            ('4', 'test'),
            ('font', 'Comic Sans'),
            ('5', '8'),
        ]

    def test_keys(self):
        config = Context()
        config['4'] = 'test'
        config['font'] = 'Comic Sans'
        config['5'] = '8'
        assert list(config.keys()) == ['4', 'font', '5']

    def test_values(self):
        config = Context()
        config['4'] = 'test'
        config['font'] = 'Comic Sans'
        config['5'] = '8'
        assert list(config.values()) == ['test', 'Comic Sans', '8']

    def test_update(self):
        one_conf_dict = {
            'key1': 'value1',
            1: 'value2',
            2: {1: 'some_value'},
        }
        another_conf_dict = {
            'key3': ('one', 'two', 'three'),
            'key4': {1: 'uno', 'key4-2': 'dos'},
        }
        merged_conf_dicts = {
            'key1': 'value1',
            1: 'value2',
            2: {1: 'some_value'},
            'key3': ('one', 'two', 'three'),
            'key4': {1: 'uno', 'key4-2': 'dos'},
        }
        config = Context(one_conf_dict)
        config.update(another_conf_dict)
        assert config == merged_conf_dicts

    def test_context_class(self):
        context = Context()
        context[1] = 'firs_value'
        context[2] = 'second_value'
        context['string_key'] = 'string_value'

        assert context[1] == 'firs_value'
        assert context[2] == 'second_value'
        assert context[3] == 'second_value'
        assert context['string_key'] == 'string_value'

    def test_initializing_context_with_context(self):
        context1 = Context({'key1': 1})
        context2 = Context(context1)
        assert context1 == context2

    def test_updating_context_with_context(self):
        context1 = Context({'key1': 1})
        context2 = Context({'key2': 2})

        context1.update(context2)
        expected_result = Context({'key1': 1, 'key2': 2})
        assert context1 == expected_result

    def test_reverse_updating_context(self):
        """Reverse update should not overwrite existing keys."""
        context1 = Context({
            'key1': 1,
            'key2': 2,
        })
        context2 = Context({
            'key2': 0,
            'key3': 0,
        })

        context1.reverse_update(context2)
        expected_result = Context({'key1': 1, 'key2': 2, 'key3': 0})
        assert context1 == expected_result


def test_importing_context_from_compiled_yml_file():
    """YAML files should be importable into the context."""
    context = Context({'section1': {'key_one': 'value_one'}})
    assert context['section1']['key_one'] == 'value_one'

    test_config_file = Path(__file__).parent / 'test_config' / 'test.yml'
    context.import_context(
        from_path=test_config_file,
        from_section='section2',
        to_section='new_section',
    )

    assert context['section1']['key_one'] == 'value_one'
    assert context['new_section']['var3'] == 'value1'

    context.import_context(
        from_path=test_config_file,
        from_section='section3',
        to_section='section3',
    )
    assert context['section3']['env_variable'] == 'test_value, hello'

    context.import_context(
        from_path=test_config_file,
        from_section='section1',
        to_section='section1',
    )
    assert context['section1']['var2'] == 'value1/value2'
    assert 'key_one' not in context['section1']


def test_instantiating_context_object_with_path():
    """Paths should be read into the context object."""
    test_context = Path(__file__).parent / 'test_config' / 'test.yml'
    context = Context(test_context)
    assert context == Context({
        'section1': {
            'var1': 'value1',
            'var2': 'value1/value2',
        },
        'section2': {
            'var3': 'value1',
            'empty_string_var': '',
        },
        'section3': {
            'env_variable': 'test_value, hello',
        },
        'section4': {
            1: 'primary_value',
        },
    })


def test_instantiating_with_directory_path(tmpdir):
    """Path directory should load context.yml."""
    test_context = Path(__file__).parent / 'test_config' / 'test.yml'
    shutil.copy(str(test_context), str(Path(tmpdir, 'context.yml')))

    context = Context(Path(tmpdir))
    assert context == Context({
        'section1': {
            'var1': 'value1',
            'var2': 'value1/value2',
        },
        'section2': {
            'var3': 'value1',
            'empty_string_var': '',
        },
        'section3': {
            'env_variable': 'test_value, hello',
        },
        'section4': {
            1: 'primary_value',
        },
    })
