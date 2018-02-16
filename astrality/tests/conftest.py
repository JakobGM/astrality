"""Application wide fixtures."""
import copy
import os
from pathlib import Path

import pytest

from astrality.config import (
    ASTRALITY_DEFAULT_GLOBAL_SETTINGS,
    generate_expanded_env_dict,
    user_configuration,
)


@pytest.fixture
def conf_path():
    """Return str path to configuration directory."""
    this_test_file = os.path.abspath(__file__)
    conf_path = Path(this_test_file).parents[1] / 'config'
    return conf_path


@pytest.fixture
def conf_file_path(conf_path):
    """Return path to example configuration."""
    return conf_path / 'astrality.yaml'


@pytest.fixture(scope='session', autouse=True)
def conf():
    """Return the configuration object for the example configuration."""
    this_test_file = os.path.abspath(__file__)
    conf_path = Path(this_test_file).parents[2]
    return user_configuration(conf_path)


@pytest.fixture
def expanded_env_dict():
    """Return expanded environment dictionary."""
    return generate_expanded_env_dict()

@pytest.fixture
def default_global_options():
    return copy.deepcopy(ASTRALITY_DEFAULT_GLOBAL_SETTINGS)
