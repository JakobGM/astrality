"""Test module for the use of external modules."""
import os
import time

import pytest

from astrality.module import ModuleManager, GlobalModulesConfig


def test_that_external_modules_are_brought_in(
    test_config_directory,
    default_global_options,
    _runtime,
):
    application_config = {
        'config/modules': {
            'modules_directory': 'test_modules',
            'enabled_modules': [
                {'name': 'thailand::thailand'},
                {'name': '*'},
            ],
        },
        'module/cambodia': {
            'enabled_modules': True,
        },
    }
    application_config.update(default_global_options)
    application_config.update(_runtime)

    module_manager = ModuleManager(application_config)

    thailand_path = test_config_directory / 'test_modules' / 'thailand'
    assert tuple(module_manager.modules.keys()) == (
        'thailand::thailand',
        'cambodia',
    )


@pytest.yield_fixture
def temp_test_files(test_config_directory):
    module_dir = test_config_directory / 'test_modules' / 'using_all_actions'
    watched_file = module_dir / 'watched_for_modifications'

    compile_target = module_dir / 'compiled.tmp'
    touch_target = module_dir / 'touched.tmp'
    watch_touch_target = module_dir / 'watch_touched.tmp'

    for file in (compile_target, touch_target, watch_touch_target,):
        if file.is_file():
            os.remove(file)

    yield compile_target, touch_target, watch_touch_target, watched_file

    for file in (compile_target, touch_target, watch_touch_target,):
        if file.is_file():
            os.remove(file)


def test_correct_relative_paths_used_in_external_module(
    temp_test_files,
    test_config_directory,
    default_global_options,
    _runtime,
):
    application_config = {
        'config/modules': {
            'modules_directory': 'test_modules',
            'enabled_modules': [{'name': 'using_all_actions::*'}],
        },
    }
    application_config.update(default_global_options)
    application_config.update(_runtime)

    module_manager = ModuleManager(application_config)

    compile_target, touch_target, watch_touch_target, watched_file = temp_test_files

    # Sanity check before testing
    for file in (compile_target, touch_target, watch_touch_target,):
        assert not file.is_file()

    # Finish task and see if context import, compilation, and run has been
    # correctly run relative to the module directory path
    module_manager.finish_tasks()
    with open(compile_target, 'r') as file:
        assert file.read() == "Vietnam's capitol is Ho Chi Minh City"
    assert touch_target.is_file()

    # Now modify the observed file, and see if on_modified is triggered
    watched_file.write_text('This watched file has been modified')
    time.sleep(0.7)

    with open(compile_target, 'r') as file:
        assert file.read() == "Vietnam's capitol is Hanoi"
    assert watch_touch_target.is_file()


def test_that_external_module_contexts_are_imported_correctly(
    test_config_directory,
    default_global_options,
    _runtime,
):
    application_config = {
        'config/modules': {
            'modules_directory': 'test_modules',
            'enabled_modules': [{'name': 'module_with_context::*', }],
        },
        'context/china': {
            'capitol': 'beijing',
        },
    }
    application_config.update(default_global_options)
    application_config.update(_runtime)

    module_manager = ModuleManager(application_config)

    expected_context = {
        'laos': {'capitol': 'vientiane'},
        'china': {'capitol': 'beijing'},
    }
    assert len(module_manager.application_context) == 2
    for key, value in expected_context.items():
        assert module_manager.application_context[key] == value
