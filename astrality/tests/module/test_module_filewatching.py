"""Tests for module manager behaviour related to file system modifications."""
import os
import shutil
from pathlib import Path
from sys import platform

import pytest

from astrality import utils
from astrality.context import Context
from astrality.module import ModuleManager
from astrality.tests.utils import Retry

MACOS = platform == 'darwin'


@pytest.yield_fixture
def modules_config(test_config_directory, temp_directory):
    empty_template = test_config_directory / 'templates' / 'empty.template'
    empty_template_target = empty_template.parent / 'empty_temp_template'
    touch_target = temp_directory / 'touched'

    secondary_template = test_config_directory \
        / 'templates' / 'no_context.template'
    secondary_template_target = temp_directory / 'secondary_template.tmp'

    modules = {
        'A': {
            'on_modified': {
                str(empty_template): {
                    'compile': [
                        {
                            'content': str(empty_template),
                            'target': str(empty_template_target),
                        },
                        {
                            'content': str(secondary_template),
                            'target': str(secondary_template_target),
                        },
                    ],
                    'run': [{'shell': 'touch ' + str(touch_target)}],
                },
            },
        },
        'B': {},
    }

    yield (
        modules,
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
    modules, empty_template, empty_template_target, touch_target, *_ \
        = modules_config
    module_manager = ModuleManager(
        modules=modules,
    )
    result = module_manager.modules['A'].execute(
        action='run',
        block='on_modified',
        path=empty_template,
    )
    assert result == (('touch ' + str(touch_target), ''),)


def test_direct_invocation_of_modifed_method_of_module_manager(modules_config):
    (
        modules,
        empty_template,
        empty_template_target,
        touch_target,
        secondary_template,
        secondary_template_target,
    ) = modules_config

    module_manager = ModuleManager(modules=modules)

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
    assert Retry()(lambda: touch_target.is_file())


@pytest.mark.slow
@pytest.mark.skipif(MACOS, reason='Flaky on MacOS')
def test_on_modified_event_in_module(modules_config):
    (
        modules,
        empty_template,
        empty_template_target,
        touch_target,
        secondary_template,
        secondary_template_target,
    ) = modules_config

    module_manager = ModuleManager(modules=modules)

    # Start the file watcher by invoking the startup command indirectly
    # through finish_tasks() method
    module_manager.finish_tasks()

    # Assert that the template file is really empty as a sanity check
    assert empty_template.read_text() == ''

    # And that target files are not created yet
    assert not touch_target.is_file()
    assert not empty_template_target.is_file()
    assert not secondary_template_target.is_file()

    # Trigger the on_modified event
    empty_template.write_text('new content')

    # And assert that the new template has been compiled
    retry = Retry()
    assert retry(lambda: empty_template_target.is_file())
    assert retry(lambda: empty_template_target.read_text() == 'new content')

    # Assert that also templates from other modules are compiled
    assert retry(lambda: secondary_template_target.is_file())
    assert retry(
        lambda: secondary_template_target.read_text() == 'one\ntwo\nthree',
    )

    # And that the new file has been touched
    assert retry(lambda: touch_target.is_file())


@pytest.yield_fixture
def test_template_targets():
    template_target1 = Path('/tmp/astrality/target1')
    template_target2 = Path('/tmp/astrality/target2')

    yield template_target1, template_target2

    if template_target1.is_file():
        os.remove(template_target1)
    if template_target2.is_file():
        os.remove(template_target2)


@pytest.mark.skipif(MACOS, reason='Flaky on MacOS')
@pytest.mark.slow
def test_hot_reloading(
    test_template_targets,
    test_config_directory,
):
    template_target1, template_target2 = test_template_targets
    config1 = test_config_directory / 'modules1.yml'
    config2 = test_config_directory / 'modules2.yml'
    target_config = test_config_directory / 'modules.yml'

    # Copy the first configuration into place
    shutil.copy(str(config1), str(target_config))

    modules1 = utils.compile_yaml(
        config1,
        context={},
    )

    application_config1 = {'astrality': {'hot_reload_config': True}}
    module_manager = ModuleManager(
        config=application_config1,
        modules=modules1,
        directory=test_config_directory,
    )

    # Before beginning, the template should not be compiled
    assert not template_target1.is_file()

    # But when we finalize tasks, it should be compiled
    module_manager.finish_tasks()
    assert template_target1.is_file()

    # Also check that the filewatcher has been started
    assert module_manager.directory_watcher.observer.is_alive()

    # We now "edit" the configuration file
    shutil.copy(str(config2), str(target_config))

    # Since hot reloading is enabled, the new template target should be
    # compiled, and the old one cleaned up
    retry = Retry()
    assert retry(lambda: template_target2.is_file())
    assert retry(lambda: not template_target1.is_file())

    # And we switch back again
    shutil.copy(str(config1), str(target_config))
    assert retry(lambda: template_target1.is_file())
    assert retry(lambda: not template_target2.is_file())

    # Cleanup config file
    if target_config.is_file():
        os.remove(target_config)

    # Stop the filewatcher
    module_manager.directory_watcher.stop()


@pytest.yield_fixture
def three_watchable_files(test_config_directory):
    file1 = test_config_directory / 'file1.tmp'
    file2 = test_config_directory / 'file2.tmp'
    file3 = test_config_directory / 'file3.tmp'

    # Delete files if they are present
    if file1.is_file():
        os.remove(file1)
    if file2.is_file():
        os.remove(file2)
    if file3.is_file():
        os.remove(file3)

    yield file1, file2, file3

    # Delete files on cleanup
    if file1.is_file():
        os.remove(file1)
    if file2.is_file():
        os.remove(file2)
    if file3.is_file():
        os.remove(file3)


@pytest.mark.skipif(MACOS, reason='Flaky on MacOS')
@pytest.mark.slow
def test_all_three_actions_in_on_modified_block(
    three_watchable_files,
    test_config_directory,
):
    file1, file2, file3 = three_watchable_files
    car_template = test_config_directory / 'templates' / 'a_car.template'
    mercedes_context = test_config_directory / 'context' / 'mercedes.yml'
    tesla_context = test_config_directory / 'context' / 'tesla.yml'

    modules = {
        'car': {
            'on_startup': {
                'import_context': {
                    'from_path': str(mercedes_context),
                },
                'compile': {
                    'content': str(car_template),
                    'target': str(file1),
                },
            },
            'on_modified': {
                str(file2): {
                    'import_context': {
                        'from_path': str(tesla_context),
                    },
                    'compile': {
                        'content': str(car_template),
                        'target': str(file1),
                    },
                    'run': {'shell': 'touch ' + str(file3)},
                },
            },
        },
    }
    module_manager = ModuleManager(modules=modules)

    # Sanity check before beginning testing
    assert not file1.is_file()
    assert not file2.is_file()
    assert not file3.is_file()

    # Now finish tasks, i.e. on_startup block
    module_manager.finish_tasks()
    assert file1.is_file()
    assert not file2.is_file()
    assert not file3.is_file()

    # Check that the correct context is inserted
    with open(file1) as file:
        assert file.read() == 'My car is a Mercedes'

    # Now modify file2 such that the on_modified block is triggered
    file2.write_text('some new content')

    # The on_modified run command should now have been executed
    assert Retry()(lambda: file3.is_file())

    module_manager.exit()


@pytest.mark.skipif(MACOS, reason='Flaky on MacOS')
@pytest.mark.slow
def test_recompile_templates_when_modified(three_watchable_files):
    template, target, _ = three_watchable_files
    template.touch()

    modules = {
        'module_name': {
            'on_startup': {
                'compile': {
                    'content': str(template),
                    'target': str(target),
                },
            },
        },
    }

    application_config = {'modules': {'reprocess_modified_files': True}}
    module_manager = ModuleManager(
        config=application_config,
        modules=modules,
        context=Context({
            'section': {1: 'value'},
        }),
    )

    # Sanity check before beginning testing
    with open(template) as file:
        assert file.read() == ''

    assert not target.is_file()

    # Compile the template
    module_manager.finish_tasks()
    with open(target) as file:
        assert file.read() == ''

    # Now write to the template and see if it is recompiled
    template.write_text('{{ section.2 }}')
    assert Retry()(lambda: target.read_text() == 'value')

    module_manager.exit()
    module_manager.directory_watcher.stop()


@pytest.mark.skipif(MACOS, reason='Flaky on MacOS')
@pytest.mark.slow
def test_recompile_templates_when_modified_overridden(
    three_watchable_files,
    test_config_directory,
):
    """
    If a file is watched in a on_modified block, it should override the
    reprocess_modified_files option.
    """
    template, target, touch_target = three_watchable_files
    template.touch()

    modules = {
        'module_name': {
            'on_startup': {
                'compile': {
                    'content': str(template),
                    'target': str(target),
                },
            },
            'on_modified': {
                str(template): {
                    'run': {'shell': 'touch ' + str(touch_target)},
                },
            },
        },
    }

    application_config = {'modules': {'reprocess_modified_files': True}}
    module_manager = ModuleManager(
        config=application_config,
        modules=modules,
        context=Context({
            'section': {1: 'value'},
        }),
        directory=test_config_directory,
    )

    # Sanity check before beginning testing
    with open(template) as file:
        assert file.read() == ''

    assert not target.is_file()

    # Compile the template
    module_manager.finish_tasks()
    with open(target) as file:
        assert file.read() == ''

    # Now write to the template and see if it is *compiled*, but the on_modified
    # command is run instead
    template.write_text('{{ section.2 }}')

    retry = Retry()
    assert retry(lambda: target.read_text() == '')
    assert retry(lambda: touch_target.is_file())

    module_manager.exit()


@pytest.mark.skipif(MACOS, reason='Flaky on MacOS')
@pytest.mark.slow
def test_importing_context_on_modification(
    three_watchable_files,
    test_config_directory,
):
    """Test that context values are imported in on_modified blocks."""
    file1, *_ = three_watchable_files
    mercedes_context = test_config_directory / 'context' / 'mercedes.yml'

    modules = {
        'module_name': {
            'on_modified': {
                str(file1): {
                    'import_context': {
                        'from_path': str(mercedes_context),
                    },
                },
            },
        },
    }
    module_manager = ModuleManager(
        modules=modules,
        context=Context({
            'car': {'manufacturer': 'Tesla'},
        }),
    )
    module_manager.finish_tasks()

    # Sanity check before modifying file1
    assert module_manager.application_context['car']['manufacturer'] == 'Tesla'

    # After modifying file1, Mercedes should have been imported
    file1.touch()
    file1.write_text('new content, resulting in importing Mercedes')
    assert Retry()(
        lambda: module_manager.application_context
        ['car']['manufacturer'] == 'Mercedes',
    )


@pytest.mark.skipif(MACOS, reason='Flaky on MacOS')
@pytest.mark.slow
def test_that_stowed_templates_are_also_watched(three_watchable_files):
    """Stowing template instead of compiling it should still be watched."""
    template, target, _ = three_watchable_files
    template.touch()

    modules = {
        'module_name': {
            'on_startup': {
                'stow': {
                    'content': str(template),
                    'target': str(target),
                    'templates': '(.+)',
                    'non_templates': 'ignore',
                },
            },
        },
    }

    application_config = {'modules': {'reprocess_modified_files': True}}
    module_manager = ModuleManager(
        config=application_config,
        modules=modules,
        context=Context({
            'section': {1: 'value'},
        }),
    )

    # Sanity check before beginning testing
    with open(template) as file:
        assert file.read() == ''

    assert not target.is_file()

    # Stow the template
    module_manager.finish_tasks()
    with open(target) as file:
        assert file.read() == ''

    # Now write to the template and see if it is recompiled
    template.write_text('{{ section.2 }}')
    assert Retry()(lambda: target.read_text() == 'value')

    module_manager.exit()
