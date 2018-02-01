"""Application wide test configuration and fixtures."""

import os
from pathlib import Path

import pytest

from config import generate_expanded_env_dict, user_configuration


def pytest_addoption(parser):
    """Add command line flags to pytest."""
    parser.addoption("--runslow", action="store_true",
                     default=False, help="run slow tests")


def pytest_collection_modifyitems(config, items):
    """Skip slow tests if not --runslow is given to pytest."""
    if config.getoption("--runslow"):
        # --runslow given in cli: do not skip slow tests
        return
    skip_slow = pytest.mark.skip(reason="need --runslow option to run")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)


@pytest.fixture
def conf_path():
    """Return str path to configuration directory."""
    this_test_file = os.path.abspath(__file__)
    conf_path = Path(this_test_file).parents[2]
    return str(conf_path)


@pytest.fixture
def conf_file_path(conf_path):
    """Return path to example configuration."""
    return os.path.join(conf_path, 'astrality.yaml.example')


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
