"""Tests for astrality.persistence.CreatedFiles."""

from pathlib import Path

from astrality.persistence import CreatedFiles, CreationMethod


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
