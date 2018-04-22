"""Tests for utils.resolve_targets."""

from pathlib import Path

from astrality.utils import resolve_targets


def test_resolving_non_existent_file():
    """When `content` does not exist, no targets should be returned."""
    targets = resolve_targets(
        content=Path('/does/not/exist'),
        target=Path('/'),
        include=r'.*',
    )
    assert targets == {}


def test_resolving_target_of_content_file():
    """When `content` is a file, the target root is used."""
    targets = resolve_targets(
        content=Path(__file__),
        target=Path('/does/not/exist'),
        include=r'.*',
    )
    assert targets == {Path(__file__): Path('/does/not/exist')}


def test_resolving_target_file_to_directory():
    """When content is a file, but target is a directory, keep filename."""
    targets = resolve_targets(
        content=Path(__file__),
        target=Path('/tmp'),
        include=r'.*',
    )
    assert targets == {Path(__file__): Path('/tmp/test_resolve_targets.py')}


def test_resolving_content_directory(tmpdir):
    """Directory hierarchy should be preserved at target."""
    temp_dir = Path(tmpdir)

    file1 = temp_dir / 'file1'
    file1.touch()

    file2 = temp_dir / 'file2'
    file2.touch()

    recursive_dir = temp_dir / 'recursive'
    recursive_dir.mkdir()

    file3 = temp_dir / 'recursive' / 'file3'
    file3.touch()

    targets = resolve_targets(
        content=temp_dir,
        target=Path('/a/b'),
        include=r'.*',
    )
    assert targets == {
        file1: Path('/a/b/file1'),
        file2: Path('/a/b/file2'),
        file3: Path('/a/b/recursive/file3'),
    }


def test_filtering_based_on_include(tmpdir):
    """Only files that match the regex should be included."""
    temp_dir = Path(tmpdir)

    file1 = temp_dir / 'file1'
    file1.touch()

    file2 = temp_dir / 'file2'
    file2.touch()

    recursive_dir = temp_dir / 'recursive'
    recursive_dir.mkdir()

    file3 = temp_dir / 'recursive' / 'file3'
    file3.touch()

    targets = resolve_targets(
        content=temp_dir,
        target=Path('/a/b'),
        include=r'.+3',
    )
    assert targets == {
        file3: Path('/a/b/recursive/file3'),
    }


def test_renaming_based_on_include(tmpdir):
    """Targets should be renameable based on the include capture group."""
    temp_dir = Path(tmpdir)

    file1 = temp_dir / 'file1'
    file1.touch()

    file2 = temp_dir / 'file2'
    file2.touch()

    recursive_dir = temp_dir / 'recursive'
    recursive_dir.mkdir()

    file3 = temp_dir / 'recursive' / 'file3'
    file3.touch()

    targets = resolve_targets(
        content=temp_dir,
        target=Path('/a/b'),
        include=r'.+(\d)',
    )
    assert targets == {
        file1: Path('/a/b/1'),
        file2: Path('/a/b/2'),
        file3: Path('/a/b/recursive/3'),
    }
