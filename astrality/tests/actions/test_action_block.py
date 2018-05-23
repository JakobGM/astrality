"""Tests for ActionBlock class."""

from pathlib import Path

from astrality.actions import ActionBlock
from astrality.context import Context


def test_null_object_pattern(global_modules_config):
    """An empty action block should have no behaviour."""
    action_block = ActionBlock(
        action_block={},
        directory=Path('/'),
        replacer=lambda x: x,
        context_store=Context(),
        global_modules_config=global_modules_config,
        module_name='test',
    )
    action_block.execute(default_timeout=1)


def test_executing_action_block_with_one_action(
    global_modules_config,
    test_config_directory,
    tmpdir,
):
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
        context_store=Context(),
        global_modules_config=global_modules_config,
        module_name='test',
    )

    action_block.execute(default_timeout=1)
    assert touched.is_file()


def test_executing_several_action_blocks(
    test_config_directory,
    tmpdir,
    global_modules_config,
):
    """Invoking execute() should execute all actions."""
    temp_dir = Path(tmpdir)
    target = temp_dir / 'target.tmp'
    touched = temp_dir / 'touched.tmp'

    action_block_dict = {
        'import_context': {'from_path': 'context/mercedes.yml'},
        'compile': [{
            'content': 'templates/a_car.template',
            'target': str(target),
        }],
        'run': {'shell': 'touch ' + str(touched)},
        'trigger': {'block': 'on_startup'},
    }
    context_store = Context()

    action_block = ActionBlock(
        action_block=action_block_dict,
        directory=test_config_directory,
        replacer=lambda x: x,
        context_store=context_store,
        global_modules_config=global_modules_config,
        module_name='test',
    )

    action_block.execute(default_timeout=1)
    assert context_store == {'car': {'manufacturer': 'Mercedes'}}
    assert target.read_text() == 'My car is a Mercedes'
    assert touched.is_file()


def test_retrieving_triggers_from_action_block(global_modules_config):
    """All trigger instructions should be returned."""
    action_block_dict = {
        'trigger': [
            {'block': 'on_startup'},
            {'block': 'on_modified', 'path': 'test.template'},
        ],
    }
    action_block = ActionBlock(
        action_block=action_block_dict,
        directory=Path('/'),
        replacer=lambda x: x,
        context_store=Context(),
        global_modules_config=global_modules_config,
        module_name='test',
    )

    startup_trigger, on_modified_trigger = action_block.triggers()

    assert startup_trigger.block == 'on_startup'
    assert on_modified_trigger.block == 'on_modified'
    assert on_modified_trigger.specified_path == 'test.template'
    assert on_modified_trigger.relative_path == Path('test.template')
    assert on_modified_trigger.absolute_path == Path('/test.template')


def test_retrieving_triggers_from_action_block_without_triggers(
    global_modules_config,
):
    """Action block with no triggers should return empty tuple."""
    action_block = ActionBlock(
        action_block={},
        directory=Path('/'),
        replacer=lambda x: x,
        context_store=Context(),
        global_modules_config=global_modules_config,
        module_name='test',
    )

    assert action_block.triggers() == tuple()


def test_retrieving_all_compiled_templates(
    global_modules_config,
    template_directory,
    tmpdir,
):
    """All earlier compilations should be retrievable."""
    template1 = template_directory / 'empty.template'
    template2 = template_directory / 'no_context.template'

    temp_dir = Path(tmpdir)
    target1 = temp_dir / 'target1.tmp'
    target2 = temp_dir / 'target2.tmp'
    target3 = temp_dir / 'target3.tmp'

    action_block_dict = {
        'compile': [
            {'content': str(template1), 'target': str(target1)},
            {'content': str(template1), 'target': str(target2)},
            {'content': str(template2), 'target': str(target3)},
        ],
    }

    action_block = ActionBlock(
        action_block=action_block_dict,
        directory=template_directory,
        replacer=lambda x: x,
        context_store=Context(),
        global_modules_config=global_modules_config,
        module_name='test',
    )

    assert action_block.performed_compilations() == {}

    action_block.execute(default_timeout=1)
    assert action_block.performed_compilations() == {
        template1: {target1, target2},
        template2: {target3},
    }


def test_symlinking(action_block_factory, create_temp_files):
    """Action blocks should symlink properly."""
    file1, file2, file3, file4 = create_temp_files(4)
    file2.write_text('original')

    action_block = action_block_factory(
        symlink=[
            {'content': str(file1), 'target': str(file2)},
            {'content': str(file3), 'target': str(file4)},
        ],
    )
    action_block.symlink()

    assert file2.is_symlink()
    assert file2.resolve() == file1
    assert file4.is_symlink()
    assert file4.resolve() == file3


def test_copying(action_block_factory, create_temp_files):
    """Action blocks should copy properly."""
    file1, file2, file3, file4 = create_temp_files(4)
    file2.write_text('original')
    file4.write_text('some other content')

    action_block = action_block_factory(
        copy=[
            {'content': str(file1), 'target': str(file2)},
            {'content': str(file3), 'target': str(file4)},
        ],
    )
    action_block.copy()

    # Check if content has been copied
    assert file2.read_text() == file1.read_text()
    assert file4.read_text() == file3.read_text()


def test_stowing(action_block_factory, create_temp_files):
    """Action blocks should stow properly."""
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
    action_block.stow()

    # Check if template has been compiled
    assert Path(target.parent / '0').read_text() == 'test_value'

    # Check if non_template has been symlinked
    assert (template.parent / 'symlink_me').resolve() == symlink_target
