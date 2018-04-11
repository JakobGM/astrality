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
    action_block.execute()

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
    }
    context_store = {}

    action_block = ActionBlock(
        action_block=action_block_dict,
        directory=test_config_directory,
        replacer=lambda x: x,
        context_store=context_store,
    )

    action_block.execute()
    assert context_store == {'car': {'manufacturer': 'Mercedes'}}
    assert target.read_text() == 'My car is a Mercedes'
    assert touched.is_file()
