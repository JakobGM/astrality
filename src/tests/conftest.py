import os

import pytest

from config import user_configuration


@pytest.fixture
def conf_path():
    this_test_file = os.path.realpath(__file__)
    return '/'.join(this_test_file.split('/')[:-3])


@pytest.fixture
def conf(conf_path):
    return user_configuration(conf_path)

