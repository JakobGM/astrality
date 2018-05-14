"""Tests for keep_running property of Module."""

from pathlib import Path

from astrality.module import Module, ModuleManager
from astrality.tests.utils import Retry


def test_module_that_does_not_need_to_keep_running():
    """on_startup block and on_exit block does not need to keep running."""
    module = Module(
        name='test',
        module_config={
            'run': {'shell': 'hi!'},
            'on_exit': {
                'run': {'shell': 'modified!'},
            },
        },
        module_directory=Path('/'),
    )
    assert module.keep_running is False


def test_module_that_needs_to_keep_running_due_to_on_modified():
    """on_modified block needs to keep running."""
    module = Module(
        name='test',
        module_config={
            'on_modified': {
                'some/path': {
                    'run': {'shell': 'modified!'},
                },
            },
        },
        module_directory=Path('/'),
    )
    assert module.keep_running is True


def test_module_that_needs_to_keep_running_due_to_on_event():
    """on_event with event listener need to keep running."""
    module = Module(
        name='test',
        module_config={
            'event_listener': {'type': 'weekday'},
            'on_event': {
                'run': {'shell': 'modified!'},
            },
        },
        module_directory=Path('/'),
    )
    assert module.keep_running is True


def test_module_without_event_listener_does_not_need_to_keep_running():
    """on_event without event listener need not to keep running."""
    module = Module(
        name='test',
        module_config={
            'on_event': {
                'run': {'shell': 'modified!'},
            },
        },
        module_directory=Path('/'),
    )
    assert module.keep_running is False


def test_that_reprocess_modified_files_causes_keep_running():
    """ModuleManager with reprocess_modified_files causes keep_running."""
    module_manager = ModuleManager(
        config={
            'modules': {
                'reprocess_modified_files': True,
            },
        },
    )
    assert module_manager.keep_running is True


def test_that_no_reprocess_modified_files_does_not_cause_keep_running():
    """ModuleManager without reprocess_modified_files does not keep_running."""
    module_manager = ModuleManager(
        config={
            'modules': {
                'reprocess_modified_files': False,
                'enabled_modules': [{'name': 'A'}],
            },
        },
        modules={'A': {}},
    )

    # We have to retry here, as processes from earlier tests might interfer
    assert Retry()(lambda: module_manager.keep_running is False)


def test_that_module_manager_asks_its_modules_if_it_should_keep_running():
    """ModuleManager should query its modules."""
    module_manager = ModuleManager(
        modules={
            'A': {'on_modified': {'some/path': {}}},
        },
    )
    assert module_manager.keep_running is True


def test_that_running_processes_causes_keep_running():
    """If shell commands are running, keep_running should be True."""
    module_manager = ModuleManager(
        modules={
            'A': {'run': {'shell': 'sleep 10'}},
        },
    )
    module_manager.finish_tasks()
    assert module_manager.keep_running is True
