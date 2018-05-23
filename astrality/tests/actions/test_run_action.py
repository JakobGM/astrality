"""Tests for RunAction."""

import logging
import os
from pathlib import Path

from astrality.actions import RunAction
from astrality.persistence import CreatedFiles


def test_null_object_pattern():
    """Null objects should be executable."""
    run_action = RunAction(
        options={},
        directory=Path('/'),
        replacer=lambda x: x,
        context_store={},
        creation_store=CreatedFiles().wrapper_for(module='test'),
    )
    run_action.execute()


def test_directory_of_executed_shell_command(tmpdir):
    """All commands should be run from `directory`."""
    temp_dir = Path(tmpdir)
    run_action = RunAction(
        options={'shell': 'touch touched.tmp', 'timeout': 1},
        directory=temp_dir,
        replacer=lambda x: x,
        context_store={},
        creation_store=CreatedFiles().wrapper_for(module='test'),
    )
    run_action.execute()
    assert (temp_dir / 'touched.tmp').is_file()


def test_that_dry_run_is_respected(tmpdir, caplog):
    """If dry_run is True, no commands should be executed, only logged."""
    temp_dir = Path(tmpdir)
    run_action = RunAction(
        options={'shell': 'touch touched.tmp', 'timeout': 1},
        directory=temp_dir,
        replacer=lambda x: x,
        context_store={},
        creation_store=CreatedFiles().wrapper_for(module='test'),
    )

    caplog.clear()
    result = run_action.execute(dry_run=True)

    # Command to be run and empty string should be returned
    assert result == ('touch touched.tmp', '')

    # Command to be run should be logged
    assert 'SKIPPED: ' in caplog.record_tuples[0][2]
    assert 'touch touched.tmp' in caplog.record_tuples[0][2]

    # Check that the command has *not* been run
    assert not (temp_dir / 'touched.tmp').is_file()


def test_use_of_replacer(tmpdir):
    """All commands should be run from `directory`."""
    temp_dir = Path(tmpdir)
    run_action = RunAction(
        options={'shell': 'whatever', 'timeout': 1},
        directory=temp_dir,
        replacer=lambda x: 'echo test',
        context_store={},
        creation_store=CreatedFiles().wrapper_for(module='test'),
    )
    command, result = run_action.execute()
    assert command == 'echo test'
    assert result == 'test'


def test_run_timeout_specified_in_action_block(tmpdir):
    """
    Run actions can time out.

    The option `timeout` overrides any timeout providided to `execute()`.
    """
    temp_dir = Path(tmpdir)
    run_action = RunAction(
        options={'shell': 'sleep 0.1 && echo hi', 'timeout': 0.05},
        directory=temp_dir,
        replacer=lambda x: x,
        context_store={},
        creation_store=CreatedFiles().wrapper_for(module='test'),
    )
    _, result = run_action.execute(default_timeout=10000)
    assert result == ''

    run_action = RunAction(
        options={'shell': 'sleep 0.1 && echo hi', 'timeout': 0.2},
        directory=temp_dir,
        replacer=lambda x: x,
        context_store={},
        creation_store=CreatedFiles().wrapper_for(module='test'),
    )
    _, result = run_action.execute(default_timeout=0)
    assert result == 'hi'


def test_run_timeout_specified_in_execute(tmpdir, caplog):
    """
    Run actions can time out, and should log this.

    The the option `timeout` is not specified, use `default_timeout` argument
    instead.
    """
    temp_dir = Path(tmpdir)
    run_action = RunAction(
        options={'shell': 'sleep 0.1 && echo hi'},
        directory=temp_dir,
        replacer=lambda x: x,
        context_store={},
        creation_store=CreatedFiles().wrapper_for(module='test'),
    )

    caplog.clear()
    _, result = run_action.execute(default_timeout=0.05)

    assert 'used more than 0.05 seconds' in caplog.record_tuples[1][2]
    assert result == ''

    run_action = RunAction(
        options={'shell': 'sleep 0.1 && echo hi'},
        directory=temp_dir,
        replacer=lambda x: x,
        context_store={},
        creation_store=CreatedFiles().wrapper_for(module='test'),
    )
    _, result = run_action.execute(default_timeout=0.2)
    assert result == 'hi'


def test_running_shell_command_with_non_zero_exit_code(caplog):
    """Shell commands with non-zero exit codes should log this."""
    run_action = RunAction(
        options={'shell': 'thiscommandshould not exist', 'timeout': 2},
        directory=Path('/'),
        replacer=lambda x: x,
        context_store={},
        creation_store=CreatedFiles().wrapper_for(module='test'),
    )
    caplog.clear()
    run_action.execute()
    assert 'not found' in caplog.record_tuples[1][2]
    assert 'non-zero return code' in caplog.record_tuples[2][2]


def test_running_shell_command_with_environment_variable(caplog):
    """Shell commands should have access to the environment."""
    run_action = RunAction(
        options={'shell': 'echo $USER', 'timeout': 2},
        directory=Path('/'),
        replacer=lambda x: x,
        context_store={},
        creation_store=CreatedFiles().wrapper_for(module='test'),
    )

    caplog.clear()
    run_action.execute()
    assert caplog.record_tuples == [
        (
            'astrality.actions',
            logging.INFO,
            f'Running command "echo {os.environ["USER"]}".',
        ),
        (
            'astrality.utils',
            logging.INFO,
            os.environ['USER'],
        ),
    ]


def test_that_environment_variables_are_expanded():
    """String parameters in any Action type should expand env variables."""
    run_action = RunAction(
        options={'shell': 'echo $EXAMPLE_ENV_VARIABLE'},
        directory=Path('/'),
        replacer=lambda x: x,
        context_store={},
        creation_store=CreatedFiles().wrapper_for(module='test'),
    )
    command, _ = run_action.execute()
    assert command == 'echo test_value'
