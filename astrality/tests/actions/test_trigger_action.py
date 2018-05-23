"""Tests for TriggerAction class."""

from pathlib import Path

from astrality.actions import TriggerAction
from astrality.persistence import CreatedFiles


def test_null_object_pattern():
    """Trigger action should be a dummy when no options are provided."""
    trigger_action = TriggerAction(
        options={},
        directory=Path('/'),
        replacer=lambda x: x,
        context_store={},
        creation_store=CreatedFiles().wrapper_for(module='test'),
    )
    trigger = trigger_action.execute()
    assert trigger is None


def test_triggering_non_on_modified_block():
    """
    Triggering a startup block should return that block.

    All path attributes should be None.
    """
    trigger_action = TriggerAction(
        options={'block': 'on_startup'},
        directory=Path('/'),
        replacer=lambda x: x,
        context_store={},
        creation_store=CreatedFiles().wrapper_for(module='test'),
    )
    trigger = trigger_action.execute()
    assert trigger.block == 'on_startup'
    assert trigger.specified_path is None
    assert trigger.relative_path is None
    assert trigger.absolute_path is None


def test_triggering_on_modified_block():
    """
    Triggering a on_modified block should return that block and path info.

    The path information contains the user-specified string path, the path
    relative to `directory`, and the absolute path.
    """
    trigger_action = TriggerAction(
        options={'block': 'on_modified', 'path': 'c/test.template'},
        directory=Path('/a/b'),
        replacer=lambda x: x,
        context_store={},
        creation_store=CreatedFiles().wrapper_for(module='test'),
    )
    trigger = trigger_action.execute()
    assert trigger.block == 'on_modified'
    assert trigger.specified_path == 'c/test.template'
    assert trigger.relative_path == Path('c/test.template')
    assert trigger.absolute_path == Path('/a/b/c/test.template')
