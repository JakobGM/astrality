"""Tests for astrality.actions.StowAction."""

from pathlib import Path

from astrality.actions import StowAction
from astrality.persistence import CreatedFiles


def test_null_object_pattern():
    """Copy actions without options should do nothing."""
    stow_action = StowAction(
        options={},
        directory=Path('/'),
        replacer=lambda x: x,
        context_store={},
        creation_store=CreatedFiles().wrapper_for(module='test'),
    )
    stow_action.execute()


def test_filtering_stowed_templates(test_config_directory, tmpdir):
    """Users should be able to restrict compilable templates with ignore."""
    temp_dir = Path(tmpdir)
    templates = \
        test_config_directory / 'test_modules' / 'using_all_actions'
    stow_dict = {
        'content': str(templates),
        'target': str(temp_dir),
        'templates': r'.+\.template',
        'non_templates': 'ignore',
    }
    stow_action = StowAction(
        options=stow_dict,
        directory=test_config_directory,
        replacer=lambda x: x,
        context_store={'geography': {'capitol': 'Berlin'}},
        creation_store=CreatedFiles().wrapper_for(module='test'),
    )

    # First testing if dry run is respected (too much work for a separate test)
    stow_action.execute(dry_run=True)
    assert len(list(temp_dir.iterdir())) == 0

    # We should have a total of two stowed files
    stow_action.execute()
    assert len(list(temp_dir.iterdir())) == 2
    assert len(list((temp_dir / 'recursive').iterdir())) == 1
    assert (temp_dir / 'module.template').is_file()
    assert (temp_dir / 'recursive' / 'empty.template').is_file()


def test_renaming_templates(test_config_directory, tmpdir):
    """Templates targets should be renameable with a capture group."""
    temp_dir = Path(tmpdir)
    templates = \
        test_config_directory / 'test_modules' / 'using_all_actions'

    # Multiple capture groups should be allowed
    stow_dict = {
        'content': str(templates),
        'target': str(temp_dir),
        'templates': r'(?:^template\.(.+)$|^(.+)\.template$)',
        'non_templates': 'ignore',
    }
    stow_action = StowAction(
        options=stow_dict,
        directory=test_config_directory,
        replacer=lambda x: x,
        context_store={'geography': {'capitol': 'Berlin'}},
        creation_store=CreatedFiles().wrapper_for(module='test'),
    )
    stow_action.execute()

    # We should have a total of two stowed files
    assert len(list(temp_dir.iterdir())) == 2
    assert len(list((temp_dir / 'recursive').iterdir())) == 1
    assert (temp_dir / 'module').is_file()
    assert (temp_dir / 'recursive' / 'empty').is_file()


def test_symlinking_non_templates(test_config_directory, tmpdir):
    """Non-templates files should be implicitly symlinked."""
    temp_dir = Path(tmpdir)
    templates = \
        test_config_directory / 'test_modules' / 'using_all_actions'
    stow_dict = {
        'content': str(templates),
        'target': str(temp_dir),
        'templates': r'.+\.template',
    }
    stow_action = StowAction(
        options=stow_dict,
        directory=test_config_directory,
        replacer=lambda x: x,
        context_store={'geography': {'capitol': 'Berlin'}},
        creation_store=CreatedFiles().wrapper_for(module='test'),
    )
    stow_action.execute()

    # Templates should still stowed
    target_dir_content = list(temp_dir.iterdir())
    assert len(target_dir_content) == 6
    assert temp_dir / 'module.template' in target_dir_content
    assert not (temp_dir / 'module.template').is_symlink()
    assert (temp_dir / 'recursive' / 'empty.template').is_file()

    # The rest should be symlinked
    assert (temp_dir / 'modules.yml').is_symlink()
    assert (temp_dir / 'modules.yml').resolve() == templates / 'modules.yml'

    # Symlinked files should be not considered as a managed file, as it is
    # self-updating.
    assert templates / 'modules.yml' not in stow_action.managed_files()


def test_copying_non_template_files(test_config_directory, tmpdir):
    """Non-templates files can be copied."""
    temp_dir = Path(tmpdir)
    templates = \
        test_config_directory / 'test_modules' / 'using_all_actions'
    stow_dict = {
        'content': str(templates),
        'target': str(temp_dir),
        'templates': r'.+\.template',
        'non_templates': 'copy',
    }
    stow_action = StowAction(
        options=stow_dict,
        directory=test_config_directory,
        replacer=lambda x: x,
        context_store={'geography': {'capitol': 'Berlin'}},
        creation_store=CreatedFiles().wrapper_for(module='test'),
    )
    stow_action.execute()

    # Templates should still stowed
    target_dir_content = list(temp_dir.iterdir())
    assert len(target_dir_content) == 6
    assert temp_dir / 'module.template' in target_dir_content
    assert (temp_dir / 'recursive' / 'empty.template').is_file()

    # The rest should be copied
    assert (temp_dir / 'modules.yml').is_file()
    assert (temp_dir / 'modules.yml').read_text() == \
        (templates / 'modules.yml').read_text()

    # Copied files should be considered as a managed file, as it needs to be
    # copied again if modified.
    assert templates / 'modules.yml' in stow_action.managed_files()
