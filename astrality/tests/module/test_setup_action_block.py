"""Tests for handling setup action blocks in ModuleManager."""

from pathlib import Path

from astrality.module import ModuleManager


def test_that_setup_block_is_only_executed_once(tmpdir):
    """Setup blocks in modules should only be performed once."""
    touched = Path(tmpdir, 'touched.tmp')
    modules = {
        'A': {
            'on_setup': {
                'run': {
                    'shell': f'touch {touched}',
                },
            },
        },
    }
    module_manager = ModuleManager(modules=modules)

    # The touched file should not exist before we have done anything
    assert not touched.exists()

    # After finishing tasks, the file should be touched
    module_manager.finish_tasks()
    assert touched.exists()

    # We now create a new object lifetime
    del module_manager
    touched.unlink()

    # The setup block should now *not* be executed
    module_manager = ModuleManager(modules=modules)
    module_manager.finish_tasks()
    assert not touched.exists()
