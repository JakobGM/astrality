"""Tests for module manager behaviour related to file system modifications."""
import os
import shutil
import time
from pathlib import Path

import pytest

from astrality.config import dict_from_config_file
from astrality.module import ModuleManager


@pytest.yield_fixture
def modules_config(
    test_config_directory,
    default_global_options,
    _runtime,
    temp_directory,
):
    empty_template = test_config_directory / 'templates' / 'empty.template'
    empty_template_target = Path('/tmp/astrality/empty_temp_template')
    touch_target = temp_directory / 'touched'

    secondary_template = test_config_directory / 'templates' / 'no_context.template'
    secondary_template_target = temp_directory / 'secondary_template.tmp'

    config = {
        'module/A': {
            'on_modified': {
                str(empty_template): {
                    'compile': [
                        {
                            'template' : str(empty_template),
                            'target': str(empty_template_target),
                        },
                        {
                            'template': str(secondary_template),
                            'target': str(secondary_template_target),
                        },
                    ],
                    'run': ['touch ' + str(touch_target)],
                },
            },
        },
        'module/B': {},
    }
    config.update(default_global_options)
    config.update(_runtime)
    yield (
        config,
        empty_template,
        empty_template_target,
        touch_target,
        secondary_template,
        secondary_template_target,
    )

    # Cleanup all test files for next test iteration
    if empty_template.is_file():
        empty_template.write_text('')
    if empty_template_target.is_file():
        os.remove(empty_template_target)
    if secondary_template_target.is_file():
        os.remove(secondary_template_target)
    if touch_target.is_file():
        os.remove(touch_target)


def test_modified_commands_of_module(modules_config):
    config, empty_template, empty_template_target, touch_target, *_= modules_config
    module_manager = ModuleManager(config)
    assert module_manager.modules['A'].modified_commands(str(empty_template)) == \
        ('touch ' + str(touch_target), )

def test_direct_invocation_of_modifed_method_of_module_manager(modules_config):
    (
        config,
        empty_template,
        empty_template_target,
        touch_target,
        secondary_template,
        secondary_template_target,
    ) = modules_config
    module_manager = ModuleManager(config)

    # PS: Disabling the directory watcher is not necessary, as it is done in
    # the startup method.

    # Now write new text to the template
    empty_template.write_text('new content')

    # And trigger the modified method manually
    module_manager.file_system_modified(empty_template)

    # And assert that the new template has been compiled
    assert empty_template_target.is_file()
    with open(empty_template_target) as file:
        assert file.read() == 'new content'

    # And that the new file has been touched
    time.sleep(0.5)
    assert touch_target.is_file()

def test_on_modified_event_in_module(modules_config):
    (
        config,
        empty_template,
        empty_template_target,
        touch_target,
        secondary_template,
        secondary_template_target,
    ) = modules_config
    module_manager = ModuleManager(config)

    # Start the file watcher by invoking the startup command indirectly
    # through finish_tasks() method
    module_manager.finish_tasks()

    # Assert that the template file is really empty as a sanity check
    with open(empty_template) as file:
        assert file.read() == ''

    # And that target files are not created yet
    assert not touch_target.is_file()
    assert not empty_template_target.is_file()
    assert not secondary_template_target.is_file()

    # Trigger the on_modified event
    empty_template.write_text('new content')
    time.sleep(1)

    # And assert that the new template has been compiled
    assert empty_template_target.is_file()
    with open(empty_template_target) as file:
        assert file.read() == 'new content'

    # Assert that also templates from other modules are compiled
    assert secondary_template_target.is_file()
    with open(secondary_template_target) as file:
        assert file.read() == 'one\ntwo\nthree'

    # And that the new file has been touched
    assert touch_target.is_file()

@pytest.yield_fixture
def test_template_targets():
    template_target1 = Path('/tmp/astrality/target1')
    template_target2 = Path('/tmp/astrality/target2')

    yield template_target1, template_target2

    if template_target1.is_file():
        os.remove(template_target1)
    if template_target2.is_file():
        os.remove(template_target2)

@pytest.mark.slow
def test_hot_reloading(
    test_template_targets,
    default_global_options,
    _runtime,
    test_config_directory
):
    template_target1, template_target2 = test_template_targets
    config1 = test_config_directory / 'astrality1.yaml'
    config2 = test_config_directory / 'astrality2.yaml'
    target_config = test_config_directory / 'astrality.yaml'
    temp_directory = Path('/tmp/astrality')

    # Copy the first configuration into place
    shutil.copy(str(config1), str(target_config))

    application_config1 = dict_from_config_file(config1)
    application_config1.update(default_global_options)
    application_config1.update(_runtime)
    application_config1['settings/astrality']['hot_reload_config'] = True

    module_manager = ModuleManager(application_config1)

    # Before beginning, the template should not be compiled
    assert not template_target1.is_file()

    # But when we finalize tasks, it should be compiled
    module_manager.finish_tasks()
    assert template_target1.is_file()

    # Also check that the filewatcher has been started
    assert module_manager.directory_watcher.observer.is_alive()

    # We now "edit" the configuration file
    shutil.copy(str(config2), str(target_config))
    time.sleep(0.7)

    # Since hot reloading is enabled, the new template target should be
    # compiled, and the old one cleaned up
    assert template_target2.is_file()
    assert not template_target1.is_file()

    # And we switch back again
    shutil.copy(str(config1), str(target_config))
    time.sleep(0.7)
    assert template_target1.is_file()
    assert not template_target2.is_file()

    # Cleanup config file
    if target_config.is_file():
        os.remove(target_config)

