"""Application wide fixtures."""
import copy
import os
import shutil
from pathlib import Path

import pytest

from astrality.config import (
    ASTRALITY_DEFAULT_GLOBAL_SETTINGS,
    user_configuration,
)
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
