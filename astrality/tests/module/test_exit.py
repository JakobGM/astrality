import os

import pytest

from astrality.module import ModuleManager


@pytest.yield_fixture
def test_target(temp_directory):
    test_target = temp_directory / 'test_target.temp'

    yield  test_target

    if test_target.is_file():
        os.remove(test_target)

def test_that_all_exit_actions_are_correctly_performed(
    default_global_options,
    _runtime,
    test_config_directory,
    test_target,
):
    application_config = {
        'module/car': {
            'on_startup': {
                'import_context': {
                    'from_path': 'context/mercedes.yml',
                },
                'compile': {
                    'template': 'templates/a_car.template',
                    'target': str(test_target),
                },
            },
            'on_exit': {
                'import_context': {
                    'from_path': 'context/tesla.yml',
                },
                'compile': {
                    'template': 'templates/a_car.template',
                    'target': str(test_target),
                },
            },
        },
    }
    application_config.update(default_global_options)
    application_config.update(_runtime)

    module_manager = ModuleManager(application_config)

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
