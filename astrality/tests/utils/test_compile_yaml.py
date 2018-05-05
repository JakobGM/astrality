"""Tests for compiling YAML jinja2 templates."""

import os
from pathlib import Path
import pytest

from astrality.config import user_configuration
from astrality.utils import compile_yaml


@pytest.yield_fixture
def dir_with_compilable_files(tmpdir):
    """Create some temporary YAML files which can be compiled."""
    config_dir = Path(tmpdir)
    config_file = config_dir / 'astrality.yml'
    config_file.write_text(
        'key1: {{ env.EXAMPLE_ENV_VARIABLE }}\n'
        'key2: {{ "echo test" | shell }}',
    )

    module_file = config_dir / 'modules.yml'
    module_file.write_text(
        'key1: {{ env.EXAMPLE_ENV_VARIABLE }}\n'
        'key2: {{ "echo test" | shell }}',
    )

    yield config_dir

    os.remove(config_file)
    os.remove(module_file)
    config_dir.rmdir()


class TestUsingConfigFilesWithPlaceholders:
    def test_dict_from_config_file(self, dir_with_compilable_files):
        """Placeholders should be properly substituted."""
        config = compile_yaml(
            path=dir_with_compilable_files / 'astrality.yml',
            context={},
        )
        assert config == {
            'key1': 'test_value',
            'key2': 'test',
        }

    def test_get_user_configuration(self, dir_with_compilable_files):
        """user_configuration should use compile_yaml properly."""
        user_conf, *_ = user_configuration(dir_with_compilable_files)
        assert user_conf['key1'] == 'test_value'
        assert user_conf['key2'] == 'test'
