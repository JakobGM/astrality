"""Tests for copying in ModuleManager."""

from pathlib import Path

from astrality.module import ModuleManager


def test_copying_in_on_modified_block(
    action_block_factory,
    create_temp_files,
    module_factory,
):
    """Module should copy properly."""
    file1, file2, file3, file4 = create_temp_files(4)
    file2.write_text('original')
    file4.write_text('some other content')

    action_block = action_block_factory(
        copy=[
            {'content': str(file1), 'target': str(file2)},
            {'content': str(file3), 'target': str(file4)},
        ],
    )
    module = module_factory(on_modified=action_block, path=Path('/a/b/c'))

    module_manager = ModuleManager()
    module_manager.modules = {'test': module}
    module_manager.on_modified(Path('/a/b/c'))

    # Check if content has been copied
    assert file2.read_text() == file1.read_text()
    assert file4.read_text() == file3.read_text()
