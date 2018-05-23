"""Tests for astrality.actions.CopyAction."""

from pathlib import Path

from astrality.actions import CopyAction
from astrality.persistence import CreatedFiles


def test_null_object_pattern():
    """Copy actions without options should do nothing."""
    copy_action = CopyAction(
        options={},
        directory=Path('/'),
        replacer=lambda x: x,
        context_store={},
        creation_store=CreatedFiles().wrapper_for(module='test'),
    )
    copy_action.execute()


def test_if_dry_run_is_respected(create_temp_files, caplog):
    """When dry_run is True, the copy action should only be logged."""
    content, target = create_temp_files(2)
    content.write_text('content')
    target.write_text('target')

    copy_action = CopyAction(
        options={'content': str(content), 'target': str(target)},
        directory=Path('/'),
        replacer=lambda x: x,
        context_store={},
        creation_store=CreatedFiles().wrapper_for(module='test'),
    )

    caplog.clear()
    result = copy_action.execute(dry_run=True)

    # We should still return the copy pair
    assert result == {content: target}

    # We should log what would have been done
    assert 'SKIPPED:' in caplog.record_tuples[0][2]
    assert str(content) in caplog.record_tuples[0][2]
    assert str(target) in caplog.record_tuples[0][2]

    # But we should not copy the file under a dry run
    assert target.read_text() == 'target'


def test_copy_action_using_all_parameters(tmpdir):
    """All three parameters should be respected."""
    temp_dir = Path(tmpdir) / 'content'
    temp_dir.mkdir()

    target = Path(tmpdir) / 'target'
    target.mkdir()

    file1 = temp_dir / 'file1'
    file1.write_text('file1 content')

    file2 = temp_dir / 'file2'
    file2.write_text('file2 content')

    recursive_dir = temp_dir / 'recursive'
    recursive_dir.mkdir()

    file3 = temp_dir / 'recursive' / 'file3'
    file3.write_text('file3 content')

    copy_options = {
        'content': str(temp_dir),
        'target': str(target),
        'include': r'file(\d)',
    }
    copy_action = CopyAction(
        options=copy_options,
        directory=temp_dir,
        replacer=lambda x: x,
        context_store={},
        creation_store=CreatedFiles().wrapper_for(module='test'),
    )
    copy_action.execute()

    assert (target / '1').read_text() == file1.read_text()
    assert (target / '2').read_text() == file2.read_text()
    assert (target / 'recursive' / '3').read_text() == file3.read_text()
    assert copy_action.copied_files == {
        file1: {target / '1'},
        file2: {target / '2'},
        file3: {target / 'recursive' / '3'},
    }
    assert file1 in copy_action


def test_copying_without_renaming(tmpdir):
    """When include is not given, keep copy name."""
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

    copy_options = {
        'content': str(temp_dir),
        'target': str(target),
    }
    copy_action = CopyAction(
        options=copy_options,
        directory=temp_dir,
        replacer=lambda x: x,
        context_store={},
        creation_store=CreatedFiles().wrapper_for(module='test'),
    )
    copy_action.execute()

    assert (target / 'file1').read_text() == file1.read_text()
    assert (target / 'file2').read_text() == file2.read_text()
    assert (target / 'recursive' / 'file3').read_text() == file3.read_text()


def test_copying_file_to_directory(tmpdir):
    """If copying from directory to file, place file in directory."""
    temp_dir = Path(tmpdir) / 'content'
    temp_dir.mkdir()

    target = Path(tmpdir) / 'target'
    target.mkdir()

    file1 = temp_dir / 'file1'
    file1.touch()

    copy_options = {
        'content': str(file1),
        'target': str(target),
        'include': r'file1',
    }
    copy_action = CopyAction(
        options=copy_options,
        directory=temp_dir,
        replacer=lambda x: x,
        context_store={},
        creation_store=CreatedFiles().wrapper_for(module='test'),
    )
    copy_action.execute()

    assert (target / 'file1').read_text() == file1.read_text()


def test_setting_permissions_on_target_copy(tmpdir):
    """If permissions is provided, use it for the target."""
    temp_dir = Path(tmpdir) / 'content'
    temp_dir.mkdir()

    target = Path(tmpdir) / 'target'
    target.mkdir()

    file1 = temp_dir / 'file1'
    file1.touch()
    file1.chmod(0o770)

    copy_options = {
        'content': str(file1),
        'target': str(target),
        'include': r'file1',
        'permissions': '777',
    }
    copy_action = CopyAction(
        options=copy_options,
        directory=temp_dir,
        replacer=lambda x: x,
        context_store={},
        creation_store=CreatedFiles().wrapper_for(module='test'),
    )
    copy_action.execute()

    assert ((target / 'file1').stat().st_mode & 0o000777) == 0o777


def test_backup_of_copy_target(create_temp_files):
    """Overwritten copy targets should be backed up."""
    target, content = create_temp_files(2)

    # This file is the original and should be backed up
    target.write_text('original')

    # This is the new content copied to target
    content.write_text('new')

    copy_options = {
        'content': str(content.name),
        'target': str(target),
    }
    copy_action = CopyAction(
        options=copy_options,
        directory=content.parent,
        replacer=lambda x: x,
        context_store={},
        creation_store=CreatedFiles().wrapper_for(module='test'),
    )

    # We replace the content by executing the action
    copy_action.execute()
    assert target.read_text() == 'new'

    # And when cleaning up the module, the backup should be restored
    CreatedFiles().cleanup(module='test')
    assert target.read_text() == 'original'
