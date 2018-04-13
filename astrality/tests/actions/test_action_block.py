"""Tests for ActionBlock class."""

from pathlib import Path

from astrality.actions import ActionBlock

def test_null_object_pattern():
    """An empty action block should have no behaviour."""
    action_block = ActionBlock(
        action_block={},
        directory=Path('/'),
        replacer=lambda x: x,
        context_store={},
    )
    action_block.execute(default_timeout=1)

def test_executing_action_block_with_one_action(test_config_directory, tmpdir):
    """Action block behaviour with only one action specified."""
    temp_dir = Path(tmpdir)
    touched = temp_dir / 'touched.tmp'

    action_block_dict = {
        'run': [{'shell': 'touch ' + str(touched)}],
    }

    action_block = ActionBlock(
        action_block=action_block_dict,
        directory=test_config_directory,
        replacer=lambda x: x,
        context_store={},
    )

    action_block.execute(default_timeout=1)
    assert touched.is_file()

def test_executing_several_action_blocks(test_config_directory, tmpdir):
    """Invoking execute() should execute all actions."""
    temp_dir = Path(tmpdir)
    target = temp_dir / 'target.tmp'
    touched = temp_dir / 'touched.tmp'

    action_block_dict = {
        'import_context': {'from_path': 'context/mercedes.yml'},
        'compile': [{
            'template': 'templates/a_car.template',
            'target': str(target),
        }],
        'run': {'shell': 'touch ' + str(touched)},
        'trigger': {'block': 'on_startup'},
    }
    context_store = {}

    action_block = ActionBlock(
        action_block=action_block_dict,
        directory=test_config_directory,
        replacer=lambda x: x,
        context_store=context_store,
    )

    action_block.execute(default_timeout=1)
    assert context_store == {'car': {'manufacturer': 'Mercedes'}}
    assert target.read_text() == 'My car is a Mercedes'
    assert touched.is_file()

def test_retrieving_triggers_from_action_block():
    """All trigger instructions should be returned."""
    action_block_dict = {
        'trigger': [
            {'block': 'on_startup'},
            {'block': 'on_modified', 'path': 'test.template'},
        ]
    }
    action_block = ActionBlock(
        action_block=action_block_dict,
        directory=Path('/'),
        replacer=lambda x: x,
        context_store={},
    )

    startup_trigger, on_modified_trigger = action_block.triggers()

    assert startup_trigger.block == 'on_startup'
    assert on_modified_trigger.block == 'on_modified'
    assert on_modified_trigger.specified_path == 'test.template'
    assert on_modified_trigger.relative_path == Path('test.template')
    assert on_modified_trigger.absolute_path == Path('/test.template')

def test_retrieving_triggers_from_action_block_without_triggers():
    """Action block with no triggers should return empty tuple."""
    action_block = ActionBlock(
        action_block={},
        directory=Path('/'),
        replacer=lambda x: x,
        context_store={},
    )

    assert action_block.triggers() == tuple()

def test_retrieving_all_compiled_templates(template_directory, tmpdir):
    """All earlier compilations should be retrievable."""
    template1 = template_directory / 'empty.template'
    template2 = template_directory / 'no_context.template'

    temp_dir = Path(tmpdir)
    target1 = temp_dir / 'target1.tmp'
    target2 = temp_dir / 'target2.tmp'
    target3 = temp_dir / 'target3.tmp'

    action_block_dict = {
        'compile': [
            {'template': str(template1), 'target': str(target1)},
            {'template': str(template1), 'target': str(target2)},
            {'template': str(template2), 'target': str(target3)},
        ],
    }

    action_block = ActionBlock(
        action_block=action_block_dict,
        directory=template_directory,
        replacer=lambda x: x,
        context_store={},
    )

    assert action_block.performed_compilations() == {}

    action_block.execute(default_timeout=1)
    assert action_block.performed_compilations() == {
        template1: {target1, target2},
        template2: {target3},
    }
