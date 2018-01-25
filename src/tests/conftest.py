import os
from pathlib import Path
import shutil

import pytest

from config import user_configuration


@pytest.fixture
def conf_path():
    this_test_file = os.path.abspath(__file__)
    conf_path = Path(this_test_file).parents[2]
    return str(conf_path)

@pytest.fixture
def conf_file_path(conf_path):
    return os.path.join(conf_path, 'astrality.conf.example')

@pytest.yield_fixture(scope='session', autouse=True)
def conf():
    this_test_file = os.path.abspath(__file__)
    conf_path = Path(this_test_file).parents[2]

    config = user_configuration(str(conf_path))
    yield config

    # Delete temporary files created by the test suite
    for file in config['conky_temp_files'].values():
        file.close()
    shutil.rmtree(config['temp_directory'])
