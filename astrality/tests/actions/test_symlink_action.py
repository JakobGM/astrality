"""Tests for astrality.actions.SymlinkAction."""

from pathlib import Path

from astrality.actions import SymlinkAction
from astrality.persistence import CreatedFiles


def test_null_object_pattern():
    """Copy actions without options should do nothing."""
    symlink_action = SymlinkAction(
        options={},
        directory=Path('/'),
        replacer=lambda x: x,
        context_store={},
        creation_store=CreatedFiles().wrapper_for(module='test'),
    )
    symlink_action.execute()


def test_symlink_dry_run(create_temp_files, caplog):
    """If dry_run is True, only log and not symlink."""
    content, target = create_temp_files(2)
    symlink_action = SymlinkAction(
        options={'content': str(content), 'target': str(target)},
        directory=Path('/'),
        replacer=lambda x: x,
        context_store={},
        creation_store=CreatedFiles().wrapper_for(module='test'),
    )

    caplog.clear()
    result = symlink_action.execute(dry_run=True)

    # We should log the symlink that had been performed
    assert 'SKIPPED:' in caplog.record_tuples[0][2]
    assert str(content) in caplog.record_tuples[0][2]
    assert str(target) in caplog.record_tuples[0][2]

    # We should also still return the intended result
    assert result == {content: target}

    # But the symlink should not be created in a dry run
    assert not target.is_symlink()


def test_symlink_action_using_all_parameters(tmpdir):
    """All three parameters should be respected."""
    temp_dir = Path(tmpdir) / 'content'
    temp_dir.mkdir()

    target = Path(tmpdir) / 'target'
    target.mkdir()

    file1 = temp_dir / 'file1'
    file1.touch()

    file2 = temp_dir / 'file2'
    file2.touch()

    recursive_dir = temp_dir / 'recursive'
    recursive_dir.mkdir()

    file3 = temp_dir / 'recursive' / 'file3'
    file3.touch()

    symlink_options = {
        'content': str(temp_dir),
        'target': str(target),
        'include': r'file(\d)',
    }
    symlink_action = SymlinkAction(
        options=symlink_options,
        directory=temp_dir,
        replacer=lambda x: x,
        context_store={},
        creation_store=CreatedFiles().wrapper_for(module='test'),
    )
    symlink_action.execute()

    assert (target / '1').is_symlink()
    assert (target / '2').is_symlink()
    assert (target / 'recursive' / '3').is_symlink()

    assert (target / '1').resolve() == file1
    assert (target / '2').resolve() == file2
    assert (target / 'recursive' / '3').resolve() == file3


def test_symlinking_without_renaming(tmpdir):
    """When include is not given, keep symlink name."""
    temp_dir = Path(tmpdir) / 'content'
    temp_dir.mkdir()

    target = Path(tmpdir) / 'target'
    target.mkdir()

    file1 = temp_dir / 'file1'
    file1.touch()

    file2 = temp_dir / 'file2'
    file2.touch()

    recursive_dir = temp_dir / 'recursive'
    recursive_dir.mkdir()

    file3 = temp_dir / 'recursive' / 'file3'
    file3.touch()

    symlink_options = {
        'content': str(temp_dir),
        'target': str(target),
    }
    symlink_action = SymlinkAction(
        options=symlink_options,
        directory=temp_dir,
        replacer=lambda x: x,
        context_store={},
        creation_store=CreatedFiles().wrapper_for(module='test'),
    )
    symlink_action.execute()

    assert (target / 'file1').is_symlink()
    assert (target / 'file2').is_symlink()
    assert (target / 'recursive' / 'file3').is_symlink()

    assert (target / 'file1').resolve() == file1
    assert (target / 'file2').resolve() == file2
    assert (target / 'recursive' / 'file3').resolve() == file3


def test_symlinking_file_to_directory(tmpdir):
    """If symlinking from directory to file, place file in directory."""
    temp_dir = Path(tmpdir) / 'content'
    temp_dir.mkdir()

    target = Path(tmpdir) / 'target'
    target.mkdir()

    file1 = temp_dir / 'file1'
    file1.touch()

    symlink_options = {
        'content': str(file1),
        'target': str(target),
        'include': r'file1',
    }
    symlink_action = SymlinkAction(
        options=symlink_options,
        directory=temp_dir,
        replacer=lambda x: x,
        context_store={},
        creation_store=CreatedFiles().wrapper_for(module='test'),
    )
    symlink_action.execute()

    assert (target / 'file1').is_symlink()
    assert (target / 'file1').resolve() == file1
    assert symlink_action.symlinked_files == {
        file1: {target / 'file1'},
    }


def test_running_symlink_action_twice(create_temp_files):
    """Symlink action should be idempotent."""
    content, target = create_temp_files(2)
    content.write_text('content')
    target.write_text('target')

    symlink_options = {
        'content': str(content),
        'target': str(target),
    }
    symlink_action = SymlinkAction(
        options=symlink_options,
        directory=content.parent,
        replacer=lambda x: x,
        context_store={},
        creation_store=CreatedFiles().wrapper_for(module='test'),
    )

    # Symlink first time
    symlink_action.execute()
    assert target.is_symlink()
    assert target.read_text() == 'content'

    # A backup shoud be created
    backup = CreatedFiles().creations['test'][str(target)]['backup']
    assert Path(backup).read_text() == 'target'

    # Symlink one more time, and assert idempotency
    symlink_action.execute()
    assert target.is_symlink()
    assert target.read_text() == 'content'

    backup = CreatedFiles().creations['test'][str(target)]['backup']
    assert Path(backup).read_text() == 'target'


def test_backup_of_symlink_target(create_temp_files):
    """Overwritten copy targets should be backed up."""
    target, content = create_temp_files(2)

    # This file is the original and should be backed up
    target.write_text('original')

    # This is the new content which will be symlinked to
    content.write_text('new')

    symlink_options = {
        'content': str(content.name),
        'target': str(target),
    }
    symlink_action = SymlinkAction(
        options=symlink_options,
        directory=content.parent,
        replacer=lambda x: x,
        context_store={},
        creation_store=CreatedFiles().wrapper_for(module='test'),
    )

    # We replace the content by executing the action
    symlink_action.execute()
    assert target.resolve().read_text() == 'new'

    # And when cleaning up the module, the backup should be restored
    CreatedFiles().cleanup(module='test')
    assert target.read_text() == 'original'
