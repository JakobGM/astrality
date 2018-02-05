"""Tests for Resolver class."""
from math import inf

import pytest

from astrality.resolver import Resolver


class TestResolverClass:
    def test_initialization_of_config_class_with_no_config_parser(self):
        Resolver()

    def test_invocation_of_class_with_application_config(self, conf):
        Resolver(conf)

    def test_initialization_of_config_class_with_dict(self):
        conf_dict = {
            'key1': 'value1',
            'key2': 'value2',
            'key3': ('one', 'two', 'three'),
            'key4': {'key4-1': 'uno', 'key4-2': 'dos'}
        }
        config = Resolver(conf_dict)
        assert config == conf_dict

    def test_values_for_max_key_property(self):
        config = Resolver()
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
        config = Resolver()
        with pytest.raises(KeyError) as exception:
            config['empty_config_with_no_key']

    def test_accessing_existing_key(self):
        config = Resolver()
        config['some_key'] = 'some_value'
        assert config['some_key'] == 'some_value'

        config[-2] = 'some_other_value'
        assert config[-2] == 'some_other_value'

    def test_integer_index_resolution(self):
        config = Resolver()
        config['some_key'] = 'some_value'
        config[1] = 'FureCode Nerd Font'
        assert config[2] == 'FureCode Nerd Font'

    def test_integer_index_resolution_without_earlier_index_key(self):
        config = Resolver()
        config['some_key'] = 'some_value'
        with pytest.raises(KeyError) as exception:
            config[2]
        assert exception.value.args[0] == \
            'Integer index "2" is non-existent and ' \
            'had no lower index to be substituted for'

    def test_index_resolution_with_string_key(self):
        config = Resolver()
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
            'key4': {1: 'uno', 'key4-2': 'dos'}
        }
        config = Resolver(conf_dict)
        assert config == conf_dict
        assert config[3][2] == 'some_value'
        assert config[2] == {1: 'some_value'}
        assert config[3] == {1: 'some_value'}

        assert isinstance(config['key4'], Resolver)
        assert config['key4'] == {1: 'uno', 'key4-2': 'dos'}
        assert config['key4'][1] == 'uno'
        assert config['key4'][2] == 'uno'

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
        config['5'] = '8'
        assert list(config.items()) == [('4', 'test',), ('font', 'Comic Sans',), ('5', '8',)]

    def test_keys(self):
        config = Resolver()
        config['4'] = 'test'
        config['font'] = 'Comic Sans'
        config['5'] = '8'
        assert list(config.keys()) == ['4', 'font', '5']

    def test_values(self):
        config = Resolver()
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
            'key4': {1: 'uno', 'key4-2': 'dos'}
        }
        merged_conf_dicts = {
            'key1': 'value1',
            1: 'value2',
            2: {1: 'some_value'},
            'key3': ('one', 'two', 'three'),
            'key4': {1: 'uno', 'key4-2': 'dos'}
        }
        config = Resolver(one_conf_dict)
        config.update(another_conf_dict)
        assert config == merged_conf_dicts

    def test_resolver_class(self):
        resolver = Resolver()
        resolver[1] = 'firs_value'
        resolver[2] = 'second_value'
        resolver['string_key'] = 'string_value'

        assert resolver[1] == 'firs_value'
        assert resolver[2] == 'second_value'
        assert resolver[3] == 'second_value'
        assert resolver['string_key'] == 'string_value'

    def test_initializing_resolver_with_resolver(self):
        resolver1 = Resolver({'key1': 1})
        resolver2 = Resolver(resolver1)
        assert resolver1 == resolver2

    def test_updating_resolver_with_resolver(self):
        resolver1 = Resolver({'key1': 1})
        resolver2 = Resolver({'key2': 2})

        resolver1.update(resolver2)
        expected_result = Resolver({'key1': 1, 'key2': 2})
        assert resolver1 == expected_result
