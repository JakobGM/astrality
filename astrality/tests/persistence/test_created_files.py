"""Tests for astrality.persistence.CreatedFiles."""

from pathlib import Path
import shutil

import pytest

from astrality.persistence import (
    CreatedFiles,
    CreationMethod,
)


def test_that_file_is_created_with_created_files():
    """A file should be created to store module created files."""
    created_files = CreatedFiles()
    path = created_files.path
    assert path.name == 'created_files.yml'
    assert path.exists()


def test_that_created_files_are_properly_persisted(create_temp_files):
    """Inserted files should be persisted properly."""
    created_files = CreatedFiles()
    # We should be able to query created files even when none have been created
    assert created_files.by(module='name') == []

    a, b, c, d = create_temp_files(4)
    # Let us start by inserting one file and see if it is returned
    created_files.insert(
        module='name',
        creation_method=CreationMethod.COPY,
        contents=[a],
        targets=[b],
    )
    assert created_files.by(module='name') == [b]

    # Insertion should be idempotent
    created_files.insert(
        module='name',
        creation_method=CreationMethod.COPY,
        contents=[a],
        targets=[b],
    )
    assert created_files.by(module='name') == [b]

    # Now insert new files
    created_files.insert(
        module='name',
        creation_method=CreationMethod.COPY,
        contents=[c],
        targets=[d],
    )
    assert created_files.by(module='name') == [b, d]

    # The content should be persisted across object lifetimes
    del created_files
    created_files = CreatedFiles()
    assert created_files.by(module='name') == [b, d]


def test_that_cleanup_method_removes_files(tmpdir, create_temp_files):
    """The cleanup method should remove all files created by module."""
    # Create some files which are made by modules
    (
        content1,
        content2,
        content3,
        content4,
        compilation1,
        compilation2,
        compilation4,
    ) = create_temp_files(7)
    symlink3 = Path(tmpdir, 'symlink3.tmp')
    symlink3.symlink_to(content3)

    # Tell CreatedFiles object that these files have been created by two
    # different modules
    created_files = CreatedFiles()
    created_files.insert(
        module='name',
        creation_method=CreationMethod.COMPILE,
        contents=[content1, content2],
        targets=[compilation1, compilation2],
    )
    created_files.insert(
        module='name',
        creation_method=CreationMethod.SYMLINK,
        contents=[content3],
        targets=[symlink3],
    )
    created_files.insert(
        module='other_module',
        creation_method=CreationMethod.COMPILE,
        contents=[content4],
        targets=[compilation4],
    )

    # Cleanup files only made by name
    created_files.cleanup(module='name')

    # Content files should be left alone
    for content in (content1, content2, content3, content4):
        assert content.exists()

    # But target files should be removed
    for cleaned_file in (compilation1, compilation2, symlink3):
        assert not cleaned_file.exists()

    # The other module should be left alone
    assert compilation4.exists()

    # No files should be persisted as created by the module afterwards
    assert created_files.by(module='name') == []

    # This should be the case between object lifetimes too
    del created_files
    created_files = CreatedFiles()
    assert created_files.by(module='name') == []


def test_that_dry_run_is_respected(create_temp_files, caplog):
    """When dry_run is True, no files should be deleted."""
    content, target = create_temp_files(2)

    created_files = CreatedFiles()
    created_files.insert(
        module='name',
        creation_method=CreationMethod.COPY,
        contents=[content],
        targets=[target],
    )

    caplog.clear()
    created_files.cleanup(module='name', dry_run=True)

    # None of the files should be affected
    assert content.exists()
    assert target.exists()

    # Skipping the deletion should be explicitly logged
    assert 'SKIPPED: ' in caplog.record_tuples[0][2]

    # And the files should still be considered created
    assert created_files.by(module='name') == [target]


def test_that_deleted_files_are_handled_gracefully_under_cleanup(
    create_temp_files,
):
    """When creations have been deleted they should be skipped."""
    content, target = create_temp_files(2)

    created_files = CreatedFiles()
    created_files.insert(
        module='name',
        creation_method=CreationMethod.COPY,
        contents=[content],
        targets=[target],
    )

    # This should be gracefully handled
    target.unlink()
    created_files.cleanup(module='name')


def test_that_inserting_non_existent_file_is_skipped(
    create_temp_files,
):
    """When creations have been deleted they should be skipped."""
    content, target = create_temp_files(2)
    target.unlink()

    created_files = CreatedFiles()
    created_files.insert(
        module='name',
        creation_method=CreationMethod.COPY,
        contents=[content],
        targets=[target],
    )

    # No file has been created!
    assert created_files.by(module='name') == []


def test_that_creations_are_properly_hashed(
    create_temp_files,
):
    """Creations should be hashed according to file content."""
    target1, target2, target3, content = create_temp_files(4)
    target1.write_text('identical')
    target2.write_text('identical')
    target3.write_text('different')

    created_files = CreatedFiles()
    created_files.insert(
        module='name',
        creation_method=CreationMethod.COPY,
        contents=[content, content, content],
        targets=[target1, target2, target3],
    )

    # These hashes should be identical
    assert created_files.creations['name'][str(target1)]['hash'] \
        == created_files.creations['name'][str(target2)]['hash']

    # But these should be different
    assert created_files.creations['name'][str(target1)]['hash'] \
        != created_files.creations['name'][str(target3)]['hash']


def test_creating_created_files_object_for_specific_module(create_temp_files):
    """You should be able to construct a CreatedFiles wrapper for a module."""
    content, target = create_temp_files(2)
    created_files = CreatedFiles().wrapper_for(module='my_module')
    created_files.insert_creation(
        content=content,
        target=target,
        method=CreationMethod.SYMLINK,
    )


def test_backup_method(tmpdir, create_temp_files, patch_xdg_directory_standard):
    """Backup should perform backup of files not created by Astrality."""
    external_file, created_file, created_file_content = create_temp_files(3)
    external_file.write_text('original')
    created_file.write_text('new')
    created_file_content.write_text('content')

    created_files = CreatedFiles()

    # A module has created a file, without a collision
    created_files.insert(
        module='name',
        creation_method=CreationMethod.COMPILE,
        contents=[created_file_content],
        targets=[created_file],
    )

    # The file should now be contained by the CreatedFiles object
    assert created_file in created_files

    # When we try to take a backup of the created file, we get None back,
    # as there is no need to perform a backup.
    assert created_files.backup(module='name', path=created_file) is None

    # The existing external file is *not* part of the created files
    assert external_file not in created_files

    # The creation should have no backup
    assert created_files.creations['name'][str(created_file)]['backup'] \
        is None

    # When we perform a backup, it is actually created
    backup = created_files.backup(module='name', path=external_file)

    # The backup contains the original filename in its new hashed filename
    assert external_file.name in backup.name

    # The content has been *moved* over
    assert backup.read_text() == 'original'
    assert not external_file.exists()

    # And the contents have been saved to the correct path
    assert backup.parent == patch_xdg_directory_standard / 'backups' / 'name'

    # The backup should now have been inserted
    assert created_files.creations['name'][str(external_file)]['backup'] \
        == str(backup)

    # If we now inform the creation, the backup info is kept
    shutil.copy2(str(created_file_content), str(external_file))
    created_files.insert(
        module='name',
        creation_method=CreationMethod.COPY,
        contents=[created_file_content],
        targets=[external_file],
    )
    assert created_files.creations['name'][str(external_file)]['backup']  \
        == str(backup)

    # But we also have the new information
    assert created_files.creations['name'][str(external_file)]['method']  \
        == 'copied'
    assert created_files.creations['name'][str(external_file)]['content'] \
        == str(created_file_content)

    # Before the cleanup, we have the new content in place
    assert external_file.read_text() == 'content'

    # But when we clean up the module, the backup should be put back in place
    created_files.cleanup('name')
    assert external_file.read_text() == 'original'


def test_taking_backup_of_symlinks(create_temp_files):
    """Symlinks should be properly backed up."""
    original_symlink, original_target, new_target = create_temp_files(3)

    # We have one existing symlink at the target location
    original_symlink.unlink()
    original_symlink.symlink_to(original_target)

    # The symlink points to original content
    original_target.write_text('original content')

    # Sanity check
    assert original_symlink.resolve() == original_target
    assert original_symlink.read_text() == 'original content'

    # We now backup the original symlink
    created_files = CreatedFiles()
    created_files.backup(module='name', path=original_symlink)

    # And we will now point it to new content
    new_target.write_text('new content')
    original_symlink.symlink_to(new_target)

    created_files.insert(
        module='name',
        creation_method=CreationMethod.SYMLINK,
        contents=[new_target],
        targets=[original_symlink],
    )

    # New sanity check
    assert original_symlink.resolve() == new_target
    assert original_symlink.read_text() == 'new content'

    # We now clean up the module and should get the original symlink back
    created_files.cleanup(module='name')
    assert original_symlink.resolve() == original_target
    assert original_symlink.read_text() == 'original content'


def test_creation_and_cleanup_of_directory(create_temp_files):
    """Created directories should be tracked."""
    # my_module is going to copy one file
    created_files = CreatedFiles().wrapper_for(module='my_module')

    # Specifically content -> target
    content, target = create_temp_files(2)

    # The target directory does not exist yet, so it creates it first
    created_files.insert_creation(
        content=None,
        target=target.parent,
        method=CreationMethod.MKDIR,
    )

    # Then copies the file over
    created_files.insert_creation(
        content=content,
        target=target,
        method=CreationMethod.COPY,
    )

    # These two creations should now be tracked
    global_created_files = CreatedFiles()
    creations = global_created_files.by('my_module')
    assert len(creations) == 2
    assert target.parent in global_created_files
    assert target in global_created_files

    # And a small sanity check, the directory actually exists
    assert target.parent.is_dir()

    # Now we introduce a small complication; an file **not** created by
    # astrality is placed within this created directory.
    external_file = target.parent / 'external.tmp'
    external_file.touch()

    # If we now clean up the module, the copied file can be deleted, but not
    # the created directory, as that would delete an external file!
    global_created_files.cleanup(module='my_module')
    assert not target.exists()
    assert target.parent.is_dir()

    # And the directory is still tracked, even after the cleanup
    assert target.parent in CreatedFiles()

    # Now we delet this external file,
    # such that the directory can be cleaned up.
    external_file.unlink()
    global_created_files.cleanup(module='my_module')
    assert not target.parent.is_dir()


def test_cleanup_of_recursive_directories(tmpdir):
    """Recursively created directories should be cleaned up."""
    tmpdir = Path(tmpdir)

    # Three recursive directories are created
    a = tmpdir / 'a'
    b = a / 'b'
    c = b / 'c'
    c.mkdir(parents=True)

    # And these creations are persisted
    created_files = CreatedFiles().wrapper_for(module='my_module')
    for directory in (c, a, b):
        created_files.insert_creation(
            content=None,
            target=directory,
            method=CreationMethod.MKDIR,
        )

    # And a file is copied over into the deepest of these directories
    content = tmpdir / 'content.tmp'
    target = c / 'target.tmp'
    content.touch()
    target.touch()
    created_files.insert_creation(
        content=content,
        target=target,
        method=CreationMethod.COPY,
    )

    # All these directories should be cleaned up
    CreatedFiles().cleanup(module='my_module')
    for directory in (a, b, c):
        assert not directory.exists()

    # Also the copied file
    assert not target.exists()


@pytest.mark.parametrize('with_wrapper', (False, True))
def test_mkdir_method_of_created_files(tmpdir, with_wrapper):
    """CreatedFiles should be able to create and persist directories."""
    tmpdir = Path(tmpdir)

    # Directory "a" already exists as a directory
    a = tmpdir / 'a'
    a.mkdir(parents=True)

    # But directory b and c are supposed to be created
    b = a / 'b'
    c = b / 'c'

    # We now want to create directory c and all parents
    created_files = CreatedFiles()

    if with_wrapper:
        created_files.wrapper_for(module='my_module').mkdir(path=c)
    else:
        created_files.mkdir(module='my_module', path=c)

    # The directories have been created
    assert b.is_dir()
    assert c.is_dir()

    # And persisted
    assert len(created_files.by('my_module')) == 2
    assert b in created_files
    assert c in created_files

    # But a should not be counted as a created directory
    assert a not in created_files

    # Cleanup should only clean b and c, but not a
    created_files.cleanup(module='my_module')
    assert not b.is_dir()
    assert not c.is_dir()
    assert a.is_dir()
