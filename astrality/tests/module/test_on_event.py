from datetime import datetime
import os

import pytest

from astrality.module import ModuleManager


@pytest.yield_fixture
def three_temporary_files(test_config_directory):
    file1 = test_config_directory / 'file1.tmp'
    file2 = test_config_directory / 'file2.tmp'
    file3 = test_config_directory / 'file3.tmp'

    yield file1, file2, file3

    if file1.is_file():
        os.remove(file1)
    if file2.is_file():
        os.remove(file2)
    if file3.is_file():
        os.remove(file3)


def test_that_only_changed_events_are_run(
    three_temporary_files,
    freezer,
):
    file1, file2, file3 = three_temporary_files

    modules = {
        'weekday': {
            'event_listener': {'type': 'weekday'},
            'on_event': {'run': {'shell': 'touch ' + str(file1)}},
        },
        'periodic': {
            'event_listener': {'type': 'periodic', 'days': 1, 'hours': 12},
            'on_event': {'run': {'shell': 'touch ' + str(file2)}},
        },
    }

    # Move to a monday
    freezer.move_to('2018-02-19')

    module_manager = ModuleManager(modules=modules)
    module_manager.finish_tasks()

    # No on_event should have been run
    assert not file1.is_file()
    assert not file2.is_file()

    # Move to a next tuesday, on day ahead
    freezer.move_to('2018-02-20')
    module_manager.finish_tasks()

    # Now the weekday module should have been run, but *not* the periodic one
    assert file1.is_file()
    assert not file2.is_file()

    # Delete the created file
    os.remove(file1)

    # Move 13 hours ahead, now the periodic timer should have been run
    freezer.move_to(datetime(
        year=2018,
        month=2,
        day=20,
        hour=13,
    ))
    module_manager.finish_tasks()

    # The periodic file should now have been created, but not the weekday one
    assert not file1.is_file()
    assert file2.is_file()

    # Now delete the two files and check if both events are detected at the
    # same time
    os.remove(file2)
    freezer.move_to('2020-01-01')
    module_manager.finish_tasks()
    assert file1.is_file()
    assert file2.is_file()
