"""Tests for the --cleanup cli flag."""

import os
from pathlib import Path

import pytest

from astrality.module import ModuleManager


@pytest.mark.parametrize('method', ['compile', 'copy', 'symlink'])
def test_that_cleanup_cli_works(
    method,
    create_temp_files,
    patch_xdg_directory_standard,
):
    """--cleanup module_name, all module created files should be deleted"""
    (
        template1,
        template2,
        template3,
        target1,
        target2,
        target3,
    ) = create_temp_files(6)

    for template in (template1, template2, template3):
        template.write_text('new content')

    for target in (target1, target2, target3):
        target.write_text('original content')

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

    for target in (target1, target2, target3):
        assert target.resolve().read_text() == 'new content'

    bin_script = str(Path(__file__).parents[3] / 'bin' / 'astrality')
    data_home = 'XDG_DATA_HOME="' + str(patch_xdg_directory_standard) + '/.." '
    command = data_home + bin_script + ' --cleanup A --cleanup B'
    os.system(command)

    for target in (target1, target2, target3):
        assert target.resolve().read_text() == 'original content'
