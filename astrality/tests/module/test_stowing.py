"""Tests for Module stow action."""

from pathlib import Path


def test_stowing(
    action_block_factory,
    create_temp_files,
    module_factory,
):
    """Module should stow properly."""
    template, target = create_temp_files(2)
    template.write_text('{{ env.EXAMPLE_ENV_VARIABLE }}')
    symlink_target = template.parent / 'symlink_me'
    symlink_target.touch()

    action_block = action_block_factory(
        stow={
            'content': str(template.parent),
            'target': str(target.parent),
            'templates': r'file(0).temp',
            'non_templates': 'symlink',
        },
    )
    module = module_factory(
        on_exit=action_block,
    )
    module.execute(action='all', block='on_exit')

    # Check if template has been compiled
    assert Path(target.parent / '0').read_text() == 'test_value'

    # Check if non_template has been symlinked
    assert (template.parent / 'symlink_me').resolve() == symlink_target
