import os
from pathlib import Path
from shutil import rmtree

import pytest

from astrality.config import (
    create_config_directory,
    resolve_config_directory,
)
from astrality.context import Context
from astrality.utils import compile_yaml


@pytest.fixture
def dummy_config():
    test_conf = Path(__file__).parents[1] / 'test_config' / 'test.yml'
    return compile_yaml(
        path=test_conf,
        context=Context(),
    )


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
            assert dummy_config['section2']['not_existing_option'] \
                is None

    def test_environment_variable_interpolation(self, dummy_config):
        assert dummy_config['section3']['env_variable'] \
            == 'test_value, hello'


class TestResolveConfigDirectory:
    def test_setting_directory_using_application_env_variable(
        self,
        monkeypatch,
    ):
        monkeypatch.setattr(
            os,
            'environ',
            {
                'ASTRALITY_CONFIG_HOME': '/test/dir',
                'XDG_CONFIG_HOME': '/xdg/dir',
            },
        )
        assert resolve_config_directory() == Path('/test/dir')

    def test_setting_directory_using_xdg_directory_standard(self, monkeypatch):
        monkeypatch.setattr(
            os,
            'environ',
            {
                'XDG_CONFIG_HOME': '/xdg/dir',
            },
        )
        assert resolve_config_directory() == Path('/xdg/dir/astrality')

    def test_using_standard_config_dir_when_nothing_else_is_specified(
        self,
        monkeypatch,
    ):
        monkeypatch.setattr(os, 'environ', {})
        assert resolve_config_directory() \
            == Path('~/.config/astrality').expanduser()


class TestCreateConfigDirectory:
    def test_creation_of_empty_config_directory(self):
        config_path = Path('/tmp/config_test')
        config_dir = create_config_directory(path=config_path, empty=True)
        assert config_path == config_dir
        assert config_dir.is_dir()
        assert len(list(config_dir.iterdir())) == 0
        config_dir.rmdir()

    def test_creation_of_infered_config_directory(self, monkeypatch):
        config_path = Path('/tmp/astrality_config')
        monkeypatch.setattr(
            os,
            'environ',
            {'ASTRALITY_CONFIG_HOME': str(config_path)},
        )
        created_config_dir = create_config_directory(empty=True)
        assert created_config_dir == config_path
        created_config_dir.rmdir()

    def test_creation_of_config_directory_with_example_content(self):
        """Test copying example configuration contents."""
        config_path = Path('/tmp/astrality_config_with_contents')
        created_config_dir = create_config_directory(config_path)
        assert created_config_dir == config_path

        # Test presence of content in created folder
        dir_contents = tuple(file.name for file in created_config_dir.iterdir())
        assert 'astrality.yml' in dir_contents
        assert 'modules' in dir_contents
        rmtree(created_config_dir)
