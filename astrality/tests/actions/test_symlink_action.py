"""Tests for astrality.actions.SymlinkAction."""

from pathlib import Path

from astrality.actions import SymlinkAction


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
    )
    symlink_action.execute()

    assert (target / 'file1').is_symlink()
    assert (target / 'file1').resolve() == file1
