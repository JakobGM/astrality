"""Application wide fixtures."""
import copy
import os
import shutil
from pathlib import Path

import pytest

from astrality.actions import ActionBlock
from astrality.config import (
    ASTRALITY_DEFAULT_GLOBAL_SETTINGS,
    user_configuration,
)
from astrality.module import Module
from astrality.utils import generate_expanded_env_dict


@pytest.fixture
def conf_path():
    """Return str path to configuration directory."""
    conf_path = Path(__file__).parents[1] / 'config'
    return conf_path


@pytest.fixture
def conf_file_path(conf_path):
    """Return path to example configuration."""
    return conf_path / 'astrality.yml'


@pytest.fixture(scope='session', autouse=True)
def conf():
    """Return the configuration object for the example configuration."""
    this_test_file = os.path.abspath(__file__)
    conf_path = Path(this_test_file).parents[1] / 'config'
    return user_configuration(conf_path)


@pytest.fixture
def expanded_env_dict():
    """Return expanded environment dictionary."""
    return generate_expanded_env_dict()


@pytest.fixture
def default_global_options():
    """Return dictionary containing all default global options."""
    return copy.deepcopy(ASTRALITY_DEFAULT_GLOBAL_SETTINGS)


@pytest.fixture
def _runtime(temp_directory, test_config_directory):
    return {'_runtime': {
        'config_directory': test_config_directory,
        'temp_directory': temp_directory,
    }}


@pytest.fixture
def test_config_directory():
    """Return path to test config directory."""
    return Path(__file__).parent / 'test_config'


@pytest.yield_fixture
def temp_directory():
    """Return path to temporary directory, and cleanup afterwards."""
    temp_dir = Path('/tmp/astrality')
    if not temp_dir.is_dir():
        os.makedirs(temp_dir)

    yield temp_dir

    # Cleanup temp dir after test has been run
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def context_directory(test_config_directory):
    """Return path to directory containing several context files."""
    return test_config_directory / 'context'


@pytest.fixture
def template_directory(test_config_directory):
    """Return path to directory containing several templates"""
    return test_config_directory / 'templates'


@pytest.fixture
def module_factory(test_config_directory):
    """Return Module factory for testing."""
    def _module_factory(
        on_startup=None,
        on_modified=None,
        path=None,
        module_directory=test_config_directory / 'test_modules' /
        'using_all_actions',
        replacer=lambda x: x,
        context_store={},
    ) -> Module:
        """Return module with specified action blocks and config."""
        module = Module(
            module_config={'module/test': {}},
            module_directory=module_directory,
            replacer=replacer,
            context_store=context_store,
        )
        if on_startup:
            module.action_blocks['on_startup'] = on_startup

        if on_modified:
            module.action_blocks['on_modified'][path] = on_modified

        return module

    return _module_factory


@pytest.fixture
def create_temp_files(tmpdir):
    """Return temp file factory function."""
    temp_dir = Path(tmpdir)

    def _create_temp_files(number):
        """Create `number` tempfiles in seperate directories and yield paths."""
        for _number in range(number):
            temp_file = temp_dir / str(_number) / f'file{_number}.temp'
            temp_file.parent.mkdir(parents=True)
            temp_file.touch()
            yield temp_file

    return _create_temp_files


@pytest.fixture
def action_block_factory(test_config_directory):
    """Return action block factory function for testing."""

    def _action_block_factory(
        compile={},
        copy={},
        run={},
        stow={},
        symlink={},
        directory=test_config_directory,
        replacer=lambda x: x,
        context_store={},
    ):
        """Return module with given parameters."""
        config = {
            'compile': compile,
            'copy': copy,
            'run': run,
            'stow': stow,
            'symlink': symlink,
        }

        return ActionBlock(
            action_block=config,
            directory=directory,
            replacer=replacer,
            context_store=context_store,
        )

    return _action_block_factory
