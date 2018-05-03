"""Tests for compile action class."""

import os
from pathlib import Path

import pytest

from astrality.actions import CompileAction


def test_null_object_pattern():
    """Compilation action with no parameters should be a null object."""
    compile_action = CompileAction(
        options={},
        directory=Path('/'),
        replacer=lambda x: x,
        context_store={},
    )
    target = compile_action.execute()
    assert target == {}


def test_compilation_of_template_to_temporary_file(template_directory):
    """Compile template to temporary file in absence of `target`."""
    compile_dict = {
        'content': 'no_context.template',
    }
    compile_action = CompileAction(
        options=compile_dict,
        directory=template_directory,
        replacer=lambda x: x,
        context_store={},
    )
    compilations = compile_action.execute()

    template = template_directory / 'no_context.template'
    assert template in compilations
    assert compilations[template].read_text() == 'one\ntwo\nthree'


def test_compilation_to_specific_absolute_file_path(template_directory, tmpdir):
    """
    Compile to specified absolute target path.

    The template is specified relatively.
    """
    target = Path(tmpdir) / 'target'
    compile_dict = {
        'content': 'no_context.template',
        'target': str(target),
    }
    compile_action = CompileAction(
        options=compile_dict,
        directory=template_directory,
        replacer=lambda x: x,
        context_store={},
    )
    return_target = list(compile_action.execute().values())[0]

    assert return_target == target
    assert target.read_text() == 'one\ntwo\nthree'


def test_compilation_to_specific_relative_file_path(template_directory, tmpdir):
    """
    Compile to specified absolute target path.

    The template is specified absolutely.
    """
    target = Path(tmpdir) / 'target'
    compile_dict = {
        'content': str(template_directory / 'no_context.template'),
        'target': str(target.name),
    }
    compile_action = CompileAction(
        options=compile_dict,
        directory=Path(tmpdir),
        replacer=lambda x: x,
        context_store={},
    )
    return_target = list(compile_action.execute().values())[0]

    assert return_target == target
    assert target.read_text() == 'one\ntwo\nthree'


def test_compilation_with_context(template_directory):
    """
    Templates should be compiled with the context store.

    It should compile differently after mutatinig the store.
    """
    compile_dict = {
        'content': 'test_template.conf',
    }
    context_store = {}

    compile_action = CompileAction(
        options=compile_dict,
        directory=template_directory,
        replacer=lambda x: x,
        context_store=context_store,
    )

    context_store['fonts'] = {2: 'ComicSans'}
    target = list(compile_action.execute().values())[0]

    username = os.environ.get('USER')
    assert target.read_text() == f'some text\n{username}\nComicSans'

    context_store['fonts'] = {2: 'TimesNewRoman'}
    target = list(compile_action.execute().values())[0]
    assert target.read_text() == f'some text\n{username}\nTimesNewRoman'


def test_setting_permissions_of_target_template(template_directory):
    """Template target permission bits should be settable."""
    compile_dict = {
        'content': 'empty.template',
        'permissions': '707',
    }
    compile_action = CompileAction(
        options=compile_dict,
        directory=template_directory,
        replacer=lambda x: x,
        context_store={},
    )

    target = list(compile_action.execute().values())[0]
    assert (target.stat().st_mode & 0o777) == 0o707


def test_use_of_replacer(template_directory, tmpdir):
    """All options should be run through the replacer."""
    compile_dict = {
        'content': 'template',
        'target': 'target',
        'permissions': 'permissions',
    }

    template = template_directory / 'no_context.template'
    target = Path(tmpdir) / 'target'

    def replacer(string: str) -> str:
        """Trivial replacer."""
        if string == 'template':
            return template.name
        elif string == 'target':
            return str(target)
        elif string == 'permissions':
            return '777'
        else:
            return string

    compile_action = CompileAction(
        options=compile_dict,
        directory=template_directory,
        replacer=replacer,
        context_store={},
    )

    target = list(compile_action.execute().values())[0]
    assert target.read_text() == 'one\ntwo\nthree'
    assert (target.stat().st_mode & 0o777) == 0o777


def test_that_current_directory_is_set_correctly(template_directory, tmpdir):
    """Shell commmand filters should be run from `directory`."""
    compile_dict = {
        'content': str(
            template_directory / 'shell_filter_working_directory.template',
        ),
    }

    directory = Path(tmpdir)
    compile_action = CompileAction(
        options=compile_dict,
        directory=directory,
        replacer=lambda x: x,
        context_store={},
    )
    target = list(compile_action.execute().values())[0]
    assert target.read_text() == tmpdir


def test_retrieving_all_compiled_templates(template_directory, tmpdir):
    """Compile actions should return all compiled templates."""
    target1, target2 = Path(tmpdir) / 'target.tmp', Path(tmpdir) / 'target2'
    targets = [target1, target2]
    template = Path('no_context.template')
    compile_dict = {
        'content': str(template),
        'target': '{target}',
    }

    # First replace {target} with target1, then with target2, by doing some
    # trickery with the replacer function.
    compile_action = CompileAction(
        options=compile_dict,
        directory=template_directory,
        replacer=lambda x: x.format(
            target=targets.pop(),
        ) if x == '{target}' else x,
        context_store={},
    )
    assert compile_action.performed_compilations() == {}

    compile_action.execute()
    assert compile_action.performed_compilations() == {
        template_directory / template: {target2},
    }

    compile_action.execute()
    assert compile_action.performed_compilations() == {
        template_directory / template: {target1, target2},
    }


def test_contains_special_method(template_directory, tmpdir):
    """Compile actions should 'contain' its compiled template."""
    temp_dir = Path(tmpdir)
    compile_dict = {
        'content': 'empty.template',
        'permissions': '707',
        'target': str(temp_dir / 'target.tmp'),
    }
    compile_action = CompileAction(
        options=compile_dict,
        directory=template_directory,
        replacer=lambda x: x,
        context_store={},
    )
    compile_action.execute()
    assert template_directory / 'empty.template' in compile_action
    assert Path('/no/template') not in compile_action


def test_contains_with_uncompiled_template(template_directory, tmpdir):
    """Compile action only contains *compiled* templates."""
    temp_dir = Path(tmpdir)
    compile_dict = {
        'content': 'empty.template',
        'permissions': '707',
        'target': str(temp_dir / 'target.tmp'),
    }
    compile_action = CompileAction(
        options=compile_dict,
        directory=template_directory,
        replacer=lambda x: x,
        context_store={},
    )
    assert template_directory / 'empty.template' not in compile_action

    compile_action.execute()
    assert template_directory / 'empty.template' in compile_action


def test_compiling_entire_directory(test_config_directory, tmpdir):
    """All directory contents should be recursively compiled."""
    temp_dir = Path(tmpdir).resolve()
    templates = \
        test_config_directory / 'test_modules' / 'using_all_actions'

    # TODO: Make this unecessary
    for file in templates.glob('**/*.tmp'):
        file.unlink()

    compile_dict = {
        'content': str(templates),
        'target': str(temp_dir),
    }
    compile_action = CompileAction(
        options=compile_dict,
        directory=test_config_directory,
        replacer=lambda x: x,
        context_store={'geography': {'capitol': 'Berlin'}},
    )
    results = compile_action.execute()

    # Check if return content is correct, showing performed compilations
    assert templates / 'module.template' in results
    assert results[templates / 'module.template'] == \
        temp_dir / 'module.template'

    # Check if the templates actually have been compiled
    target_dir_content = list(temp_dir.iterdir())
    assert len(target_dir_content) == 6
    assert temp_dir / 'module.template' in target_dir_content
    assert (temp_dir / 'recursive' / 'empty.template').is_file()


def test_filtering_compiled_templates(test_config_directory, tmpdir):
    """Users should be able to restrict compilable templates."""
    temp_dir = Path(tmpdir)
    templates = \
        test_config_directory / 'test_modules' / 'using_all_actions'
    compile_dict = {
        'content': str(templates),
        'target': str(temp_dir),
        'include': r'.+\.template',
    }
    compile_action = CompileAction(
        options=compile_dict,
        directory=test_config_directory,
        replacer=lambda x: x,
        context_store={'geography': {'capitol': 'Berlin'}},
    )
    compile_action.execute()

    # We should have a total of two compiled files
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
    compile_dict = {
        'content': str(templates),
        'target': str(temp_dir),
        'include': r'(?:^template\.(.+)$|^(.+)\.template$)',
    }
    compile_action = CompileAction(
        options=compile_dict,
        directory=test_config_directory,
        replacer=lambda x: x,
        context_store={'geography': {'capitol': 'Berlin'}},
    )
    compile_action.execute()

    # We should have a total of two compiled files
    assert len(list(temp_dir.iterdir())) == 2
    assert len(list((temp_dir / 'recursive').iterdir())) == 1
    assert (temp_dir / 'module').is_file()
    assert (temp_dir / 'recursive' / 'empty').is_file()
