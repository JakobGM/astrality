import os
import shutil

import pytest

from config import user_configuration


@pytest.fixture
def conf_path():
    this_test_file = os.path.realpath(__file__)
    conf_path = '/'.join(this_test_file.split('/')[:-3])
    return conf_path


@pytest.yield_fixture(scope='session', autouse=True)
def conf():
    this_test_file = os.path.realpath(__file__)
    conf_path = '/'.join(this_test_file.split('/')[:-3])
    config = user_configuration(conf_path)
    yield config

    # Delete temporary files created by the test suite
    for file in config['conky-temp-files'].values():
        file.close()
    shutil.rmtree(config['temp-directory'])
