"""Tests for ImportContextAction class."""

from astrality.actions import ImportContextAction

def test_resolving_relative_paths(context_directory):
    """From path should be converted to absolute path relative to directory."""
    context_import_dict = {
        'from_path': 'mercedes.yml',
    }
    context_store = {}
    import_context_action = ImportContextAction(
        options=context_import_dict,
        directory=context_directory,
        replacer=lambda x: x,
        context_store=context_store,
    )
    assert import_context_action.from_path == \
        context_directory / 'mercedes.yml'

def test_importing_entire_file(context_directory):
    """
    Test importing all sections from context file.

    All context sections should be imported in the absence of `from_section`.
    """
    context_import_dict = {
        'from_path': 'several_sections.yml',
    }
    context_store = {}
    import_context_action = ImportContextAction(
        options=context_import_dict,
        directory=context_directory,
        replacer=lambda x: x,
        context_store=context_store,
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
        }
    }
    assert context_store == expected_context

def test_importing_specific_section(context_directory):
    """Test importing specific sections from context file."""
    context_import_dict = {
        'from_path': 'several_sections.yml',
        'from_section': 'section1',
    }
    context_store = {'original': 'value'}
    import_context_action = ImportContextAction(
        options=context_import_dict,
        directory=context_directory,
        replacer=lambda x: x,
        context_store=context_store,
    )
    import_context_action.execute()

    expected_context = {
        'original': 'value',
        'section1': {
            'k1_1': 'v1_1',
            'k1_2': 'v1_2',
        },
    }
    assert context_store == expected_context
