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
