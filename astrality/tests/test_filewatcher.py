import os
import shutil
import time
from pathlib import Path

import pytest

from astrality.filewatcher import DirectoryWatcher


@pytest.yield_fixture
def test_files():
    """Return paths related to two test files and cleanup afterwards."""
    watched_directory = Path('/tmp/astrality')
    test_file1 = watched_directory / 'tmp_test_file1'

    recursive_dir = watched_directory / 'test_folder'
    test_file2 = recursive_dir / 'tmp_test_file2'

    yield watched_directory, recursive_dir, test_file1, test_file2

    # Cleanup files
    if test_file1.is_file():
        os.remove(test_file1)
    if test_file2.is_file():
        os.remove(test_file2)
    if recursive_dir.is_dir():
        shutil.rmtree(recursive_dir)


@pytest.yield_fixture
def watch_dir():
    """Instanciate a directory watcher and stop it after its use."""
    class EventSaver:
        """Mock class for testing callback function."""

        def __init__(self):
            self.called = 0

        def save_argument(self, path: Path) -> None:
            self.called += 1
            self.argument = path

    event_saver = EventSaver()

    # Watch a temporary directory
    watched_directory = Path('/tmp/astrality')
    dir_watcher = DirectoryWatcher(
        directory=watched_directory,
        on_modified=event_saver.save_argument,
    )

    yield dir_watcher, event_saver

    dir_watcher.stop()


@pytest.mark.slow
def test_filesystem_watcher(test_files, watch_dir):
    """
    Test correct callback invocation on directory watching.

    Sometimes the on_modified function is called several times by watchdog,
    for a unknown reason. It might be other tests which interfer. We therefore
    check if the lower bound of calls is satisfied, but do not test the exact
    number of calls to on_modified.
    """
    watched_directory, recursive_dir, test_file1, test_file2 = test_files
    dir_watcher, event_saver = watch_dir

    # Start watching the directory
    dir_watcher.start()

    # Nothing has been modified yet
    assert not hasattr(event_saver, 'argument')
    assert event_saver.called == 0

    # Create an empty file
    test_file1.touch()

    # New files are not considered "modified"
    time.sleep(0.7)
    assert not hasattr(event_saver, 'argument')
    assert event_saver.called == 0

    # But when we write to it, it is considered "modified"
    with open(test_file1, 'w') as file:
        file.write('test_content')

    time.sleep(0.7)
    assert event_saver.argument == test_file1
    assert event_saver.called >= 1

    # Create a directory in the watched directory
    recursive_dir.mkdir(parents=True)

    # Subdirectories are not of interest
    time.sleep(0.7)
    assert event_saver.argument == test_file1
    assert event_saver.called >= 1

    # Create a file in the subdirectory
    test_file2.write_text('test')

    # Both the touch event and the write event are considered of interest
    time.sleep(0.7)
    assert event_saver.argument == test_file2
    assert event_saver.called >= 2
