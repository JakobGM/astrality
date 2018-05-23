import os
from pathlib import Path

import pytest

from astrality.module import ModuleManager


@pytest.yield_fixture
def test_target(tmpdir):
    test_target = Path(tmpdir) / 'test_target.temp'

    yield test_target

    if test_target.is_file():
        os.remove(test_target)


@pytest.mark.slow
def test_that_all_exit_actions_are_correctly_performed(
    test_config_directory,
    test_target,
):
    modules = {
        'car': {
            'on_startup': {
                'import_context': {
                    'from_path': 'context/mercedes.yml',
                },
                'compile': {
                    'content': 'templates/a_car.template',
                    'target': str(test_target),
                },
            },
            'on_exit': {
                'import_context': {
                    'from_path': 'context/tesla.yml',
                },
                'compile': {
                    'content': 'templates/a_car.template',
                    'target': str(test_target),
                },
            },
        },
    }

    module_manager = ModuleManager(modules=modules)

    # Before we start, the template target should not exist
    assert not test_target.is_file()

    # We finish tasks, reslulting in Mercedes being compiled
    module_manager.finish_tasks()
    with open(test_target) as file:
        assert file.read() == 'My car is a Mercedes'

    # We now exit, and check if the context import and compilation has been
    # performed
    module_manager.exit()
    with open(test_target) as file:
        assert file.read() == 'My car is a Tesla'
