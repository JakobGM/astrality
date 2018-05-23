"""Test module for the use of external modules."""
import os
from sys import platform

import pytest

from astrality.context import Context
from astrality.module import ModuleManager
from astrality.tests.utils import Retry


MACOS = platform == 'darwin'


def test_that_external_modules_are_brought_in(test_config_directory):
    application_config = {
        'modules': {
            'modules_directory': 'test_modules',
            'enabled_modules': [
                {'name': 'thailand::thailand'},
                {'name': '*'},
            ],
        },
    }

    modules = {
        'cambodia': {
            'enabled_modules': True,
        },
    }
    module_manager = ModuleManager(
        config=application_config,
        modules=modules,
    )

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

    for file in (compile_target, touch_target, watch_touch_target):
        if file.is_file():
            os.remove(file)

    yield compile_target, touch_target, watch_touch_target, watched_file

    for file in (compile_target, touch_target, watch_touch_target):
        if file.is_file():
            os.remove(file)


@pytest.mark.slow
@pytest.mark.skipif(MACOS, reason='Flaky on MacOS')
def test_correct_relative_paths_used_in_external_module(
    temp_test_files,
    test_config_directory,
):
    application_config = {
        'modules': {
            'modules_directory': 'test_modules',
            'enabled_modules': [{'name': 'using_all_actions::*'}],
        },
    }
    module_manager = ModuleManager(config=application_config)

    (
        compile_target,
        touch_target,
        watch_touch_target,
        watched_file,
    ) = temp_test_files

    # Sanity check before testing
    for file in (compile_target, touch_target, watch_touch_target):
        assert not file.is_file()

    # Finish task and see if context import, compilation, and run has been
    # correctly run relative to the module directory path
    module_manager.finish_tasks()
    with open(compile_target, 'r') as file:
        assert file.read() == "Vietnam's capitol is Ho Chi Minh City"
    assert touch_target.is_file()

    # Now modify the observed file, and see if on_modified is triggered
    watched_file.write_text('This watched file has been modified')

    retry = Retry()
    assert retry(
        lambda: compile_target.read_text() == "Vietnam's capitol is Hanoi",
    )
    assert retry(lambda: watch_touch_target.is_file())

    touch_target.unlink()
    compile_target.unlink()
    watch_touch_target.unlink()
    watched_file.write_text('')


def test_that_external_module_contexts_are_imported_correctly(
    test_config_directory,
):
    application_config = {
        'modules': {
            'modules_directory': 'test_modules',
            'enabled_modules': [{'name': 'module_with_context::*'}],
        },
    }

    context = Context({
        'china': {
            'capitol': 'beijing',
        },
    })
    module_manager = ModuleManager(
        config=application_config,
        context=context,
    )

    expected_context = Context({
        'laos': {'capitol': 'vientiane'},
        'china': {'capitol': 'beijing'},
    })
    assert module_manager.application_context == expected_context
