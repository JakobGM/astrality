"""Tests for ImportContextAction class."""

from pathlib import Path

from astrality.actions import ImportContextAction
from astrality.context import Context
from astrality.persistence import CreatedFiles


def test_null_object_pattern():
    """Test initializing action with no behaviour."""
    import_context_action = ImportContextAction(
        options={},
        directory=Path('/'),
        replacer=lambda x: x,
        context_store=Context(),
        creation_store=CreatedFiles().wrapper_for(module='test'),
    )
    import_context_action.execute()


def test_importing_entire_file(context_directory):
    """
    Test importing all sections from context file.

    All context sections should be imported in the absence of `from_section`.
    """
    context_import_dict = {
        'from_path': 'several_sections.yml',
    }
    context_store = Context()
    import_context_action = ImportContextAction(
        options=context_import_dict,
        directory=context_directory,
        replacer=lambda x: x,
        context_store=context_store,
        creation_store=CreatedFiles().wrapper_for(module='test'),
    )
    import_context_action.execute()

    expected_context = {
        'section1': {
            'k1_1': 'v1_1',
            'k1_2': 'v1_2',
        },
        'section2': {
            'k2_1': 'v2_1',
            'k2_2': 'v2_2',
        },
    }
    assert context_store == expected_context


def test_importing_specific_section(context_directory):
    """Test importing specific sections from context file."""
    context_import_dict = {
        'from_path': 'several_sections.yml',
        'from_section': 'section1',
    }
    context_store = Context({'original': 'value'})
    import_context_action = ImportContextAction(
        options=context_import_dict,
        directory=context_directory,
        replacer=lambda x: x,
        context_store=context_store,
        creation_store=CreatedFiles().wrapper_for(module='test'),
    )
    import_context_action.execute()

    expected_context = Context({
        'original': 'value',
        'section1': {
            'k1_1': 'v1_1',
            'k1_2': 'v1_2',
        },
    })
    assert context_store == expected_context


def test_replacer_function_being_used(context_directory):
    """
    Test use of replacement function in option retrieval.

    The function should be used when querying values from `options`.
    """
    context_import_dict = {
        'from_path': 'path',
        'from_section': 'from',
        'to_section': 'to',
    }
    context_store = Context()

    def replacer(option: str) -> str:
        if option == 'path':
            return 'several_sections.yml'
        elif option == 'from':
            return 'section1'
        elif option == 'to':
            return 'new_section'
        else:
            raise AssertionError

    import_context_action = ImportContextAction(
        options=context_import_dict,
        directory=context_directory,
        replacer=replacer,
        context_store=context_store,
        creation_store=CreatedFiles().wrapper_for(module='test'),
    )
    import_context_action.execute()

    assert context_store == {
        'new_section': {
            'k1_1': 'v1_1',
            'k1_2': 'v1_2',
        },
    }


def test_that_replacer_is_run_every_time(context_directory):
    """
    The replacer should be run a new every time self.execute() is invoked.
    """
    context_import_dict = {
        'from_path': 'several_sections.yml',
        'from_section': 'section1',
        'to_section': 'whatever',
    }
    context_store = Context()

    class Replacer:
        def __init__(self) -> None:
            self.invoke_number = 0

        def __call__(self, option: str) -> str:
            self.invoke_number += 1
            return option

    replacer = Replacer()
    import_context_action = ImportContextAction(
        options=context_import_dict,
        directory=context_directory,
        replacer=replacer,
        context_store=context_store,
        creation_store=CreatedFiles().wrapper_for(module='test'),
    )

    import_context_action.execute()
    assert replacer.invoke_number == 3

    import_context_action.execute()
    assert replacer.invoke_number == 6
