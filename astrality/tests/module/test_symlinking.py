"""Tests for symlink actions in Module object."""


def test_symlinking_in_on_startup_block(
    action_block_factory,
    module_factory,
    create_temp_files,
):
    """Action blocks should symlink properly."""
    file1, file2, file3, file4 = create_temp_files(4)
    file2.write_text('original')

    action_block = action_block_factory(
        symlink=[
            {'content': str(file1), 'target': str(file2)},
            {'content': str(file3), 'target': str(file4)},
        ],
    )
    module = module_factory(on_startup=action_block)
    module.execute(action='all', block='on_startup')

    assert file2.is_symlink()
    assert file2.resolve() == file1
    assert file4.is_symlink()
    assert file4.resolve() == file3
