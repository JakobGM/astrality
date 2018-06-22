"""Tests for locating and parsing YAML configuration files."""
import os
from pathlib import Path
from shutil import rmtree

import pytest

from astrality.config import (
    ASTRALITY_DEFAULT_GLOBAL_SETTINGS,
    create_config_directory,
    infer_config_location,
    resolve_config_directory,
    user_configuration,
)
from astrality.context import Context
from astrality.utils import compile_yaml, dump_yaml


@pytest.fixture
def dummy_config():
    """Return dummy configuration YAML file."""
    test_conf = Path(__file__).parents[1] / 'test_config' / 'test.yml'
    return compile_yaml(
        path=test_conf,
        context=Context(),
    )


class TestAllConfigFeaturesFromDummyConfig:
    """Tests for .utils.compile_yaml."""

    def test_normal_variable(self, dummy_config):
        """String literals should be interpreted without modifications."""
        assert dummy_config['section1']['var1'] == 'value1'
        assert dummy_config['section1']['var2'] == 'value1/value2'
        assert dummy_config['section2']['var3'] == 'value1'

    def test_empty_string_variable(self, dummy_config):
        """Empty strings  should be representable."""
        assert dummy_config['section2']['empty_string_var'] == ''

    def test_non_existing_variable(self, dummy_config):
        """Non-existing keys should not have defaults but raise instead."""
        with pytest.raises(KeyError):
            assert dummy_config['section2']['not_existing_option'] \
                is None

    def test_environment_variable_interpolation(self, dummy_config):
        """Environment variables should be interpolated with Jinja syntax."""
        assert dummy_config['section3']['env_variable'] \
            == 'test_value, hello'


class TestResolveConfigDirectory:
    """Tests for .config.resolve_config_directory."""

    def test_setting_directory_using_application_env_variable(
        self,
        monkeypatch,
    ):
        """ASTRALITY_CONFIG_HOME should override XDG_CONFIG_HOME."""
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
        """The XDG_CONFIG_HOME environment variable should be respected."""
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
        """In the absence of XDG_CONFIG_HOME, the standard location is used."""
        monkeypatch.setattr(os, 'environ', {})
        assert resolve_config_directory() \
            == Path('~/.config/astrality').expanduser()


class TestCreateConfigDirectory:
    """Tests for creating configuration content, used be the CLI entrypoint."""

    def test_creation_of_empty_config_directory(self):
        """An empty configuration directory can be created."""
        config_path = Path('/tmp/config_test')
        config_dir = create_config_directory(path=config_path, empty=True)

        assert config_path == config_dir
        assert config_dir.is_dir()
        assert len(list(config_dir.iterdir())) == 0

        config_dir.rmdir()

    def test_creation_of_infered_config_directory(self, monkeypatch):
        """When no directory is specified, it is inferred instead."""
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


class TestInferConfigLocation:
    """Tests for config.infer_config_location()."""

    def test_that_empty_config_location_still_return_paths(
        self,
        monkeypatch,
        caplog,
    ):
        """
        A lack of astrality.yml should not change the result.

        When astrality.yml is not found in the configuration directory, a
        warning should be logged, but the path should still be returned.
        The remaining logic should use default values for astrality.yml instead.
        """
        config_path = Path('/tmp/astrality_config')
        monkeypatch.setattr(
            os,
            'environ',
            {'ASTRALITY_CONFIG_HOME': str(config_path)},
        )
        caplog.clear()
        directory, config_file = infer_config_location()
        assert directory == config_path
        assert config_file == config_path / 'astrality.yml'
        assert 'not found' in caplog.record_tuples[0][2]


class TestUserConfiguration:
    """Tests for config.user_configuration()."""

    def test_missing_global_configuration_file(self, monkeypatch, tmpdir):
        """Missing astrality.yml should result in default values."""
        # Create directory used as astrality config directory
        config_home = Path(tmpdir)
        monkeypatch.setattr(
            os,
            'environ',
            {'ASTRALITY_CONFIG_HOME': str(config_home)},
        )

        # Sanity check
        assert len(list(config_home.iterdir())) == 0

        # Create modules and context files, but *not* astrality.yml
        modules = {'A': {'enabled': False}}
        dump_yaml(path=config_home / 'modules.yml', data=modules)

        context = {'section': {'key': 'value'}}
        dump_yaml(path=config_home / 'context.yml', data=context)

        (
            global_config,
            global_modules,
            global_context,
            inferred_path,
        ) = user_configuration()
        assert global_config == ASTRALITY_DEFAULT_GLOBAL_SETTINGS
        assert global_modules == modules
        assert global_context == context
        assert inferred_path == config_home
