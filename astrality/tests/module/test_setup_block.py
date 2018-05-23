"""Tests for setup block in module."""

from pathlib import Path

from astrality.actions import SetupActionBlock
from astrality.module import Module


def test_that_module_block_is_persisted():
    """Module should create a 'setup' action block."""
    module_config = {
        'on_setup': {
            'run': {
                'shell': 'echo first time!',
            },
        },
    }
    params = {
        'name': 'test',
        'module_config': module_config,
        'module_directory': Path(__file__).parent,
    }

    module = Module(**params)
    assert isinstance(
        module.get_action_block(name='on_setup'),
        SetupActionBlock,
    )
    assert module.execute(action='run', block='on_setup') == (
        ('echo first time!', 'first time!'),
    )

    # After creating this module again, the run action should not be performed.
    del module
    module = Module(**params)
    assert module.execute(action='run', block='on_setup') == tuple()
