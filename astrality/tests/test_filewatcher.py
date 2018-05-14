import os
import shutil
from sys import platform
from pathlib import Path

import pytest

from astrality.filewatcher import DirectoryWatcher
from astrality.tests.utils import Retry


MACOS = platform == 'darwin'


@pytest.yield_fixture
def watch_dir(tmpdir):
    """Instanciate a directory watcher and stop it after its use."""
    watched_directory = Path(tmpdir)
    test_file1 = watched_directory / 'tmp_test_file1'
    recursive_dir = watched_directory / 'test_folder'
    test_file2 = recursive_dir / 'tmp_test_file2'

    class EventSaver:
        """Mock class for testing callback function."""

        def __init__(self):
            self.called = 0
            self.argument = None

        def save_argument(self, path: Path) -> None:
            self.called += 1
            self.argument = path

    event_saver = EventSaver()

    # Watch a temporary directory
    dir_watcher = DirectoryWatcher(
        directory=watched_directory,
        on_modified=event_saver.save_argument,
    )

    yield (
        watched_directory,
        recursive_dir,
        test_file1,
        test_file2,
        dir_watcher,
        event_saver,
    )

    dir_watcher.stop()

    # Cleanup files
    if test_file1.is_file():
        os.remove(test_file1)
    if test_file2.is_file():
        os.remove(test_file2)
    if recursive_dir.is_dir():
        shutil.rmtree(recursive_dir)


@pytest.mark.skipif(MACOS, reason='Flaky on MacOS')
@pytest.mark.slow
def test_filesystem_watcher(watch_dir):
    """
    Test correct callback invocation on directory watching.

    Sometimes the on_modified function is called several times by watchdog,
    for a unknown reason. It might be other tests which interfer. We therefore
    check if the lower bound of calls is satisfied, but do not test the exact
    number of calls to on_modified.
    """
    (
        watched_directory,
        recursive_dir,
        test_file1,
        test_file2,
        dir_watcher,
        event_saver,
    ) = watch_dir

    # Start watching the directory
    dir_watcher.start()

    # Nothing has been modified yet
    assert event_saver.argument is None
    assert event_saver.called == 0

    # Create an empty file
    test_file1.touch()

    # We might have to try several times, as filewatching can be slow
    retry = Retry()

    # New files are not considered "modified"
    assert event_saver.argument is None
    assert event_saver.called == 0

    # But when we write to it, it is considered "modified"
    test_file1.write_text('test_content')

    assert retry(lambda: event_saver.argument == test_file1)
    assert event_saver.called >= 1

    # Create a directory in the watched directory
    recursive_dir.mkdir(parents=True)

    # Subdirectories are not of interest
    assert retry(lambda: event_saver.argument == test_file1)
    assert retry(lambda: event_saver.called >= 1)

    # Create a file in the subdirectory
    test_file2.write_text('test')

    # Both the touch event and the write event are considered of interest
    assert retry(lambda: event_saver.argument == test_file2)
    assert event_saver.called == 2
