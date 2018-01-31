import os
from pathlib import Path
import shutil

import pytest

from config import user_configuration

def pytest_addoption(parser):
    parser.addoption("--runslow", action="store_true",
                     default=False, help="run slow tests")

def pytest_collection_modifyitems(config, items):
    if config.getoption("--runslow"):
        # --runslow given in cli: do not skip slow tests
        return
    skip_slow = pytest.mark.skip(reason="need --runslow option to run")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)

@pytest.fixture
def conf_path():
    this_test_file = os.path.abspath(__file__)
    conf_path = Path(this_test_file).parents[2]
    return str(conf_path)

@pytest.fixture
def conf_file_path(conf_path):
    return os.path.join(conf_path, 'astrality.yaml.example')

@pytest.yield_fixture(scope='session', autouse=True)
def conf():
    this_test_file = os.path.abspath(__file__)
    conf_path = Path(this_test_file).parents[2]

    config = user_configuration(conf_path)
    yield config

    # Delete temporary files created by the test suite
    # TODO: ModuleManager exit handler
    shutil.rmtree(config['_runtime']['temp_directory'])
