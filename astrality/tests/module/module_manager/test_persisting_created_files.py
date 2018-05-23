"""Tests for ensuring that all files that are created are persisted."""

import pytest

from astrality.module import ModuleManager
from astrality.persistence import CreatedFiles


@pytest.mark.parametrize('method', ['compile', 'copy', 'symlink'])
def test_that_created_files_are_persisted(method, create_temp_files):
    """When modules create files, they should be persisted."""
    (
        template1,
        template2,
        template3,
        target1,
        target2,
        target3,
    ) = create_temp_files(6)

    # Delete targets to prevent backups from being restored
    for target in (target1, target2, target3):
        target.unlink()

    modules = {
        'A': {
            method: [
                {
                    'content': str(template1),
                    'target': str(target1),
                },
                {
                    'content': str(template2),
                    'target': str(target2),
                },
            ],
        },
        'B': {
            method: {
                'content': str(template3),
                'target': str(target3),
            },
        },
    }
    module_manager = ModuleManager(modules=modules)
    module_manager.finish_tasks()

    created_files = CreatedFiles()
    assert created_files.by(module='A') == [target1, target2]
    assert created_files.by(module='B') == [target3]

    # Now we should be able to cleanup the created files
    assert target1.exists()
    assert target2.exists()
    assert target3.exists()

    # First let's see if dry run is respected
    created_files.cleanup(module='A', dry_run=True)
    assert target1.exists()
    assert target2.exists()
    assert target3.exists()
    assert created_files.by(module='A') == [target1, target2]
    assert created_files.by(module='B') == [target3]

    # Now see if we can cleanup module A and let B stay intact
    created_files.cleanup(module='A')
    assert not target1.exists()
    assert not target2.exists()
    assert target3.exists()
    assert created_files.by(module='A') == []
    assert created_files.by(module='B') == [target3]

    # Now all files should be cleaned
    created_files.cleanup(module='B')
    assert not target3.exists()
    assert created_files.by(module='A') == []
    assert created_files.by(module='B') == []

    # Let's see if it has been properly persisted too
    del created_files
    created_files = CreatedFiles()
    assert created_files.by(module='A') == []
    assert created_files.by(module='B') == []
