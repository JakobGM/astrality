"""Tests for RunAction."""

from pathlib import Path

from astrality.actions import RunAction

def test_null_object_pattern():
    """Null objects should be executable."""
    run_action = RunAction(
        options={},
        directory=Path('/'),
        replacer=lambda x: x,
        context_store={},
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
    )
    run_action.execute()
    assert (temp_dir / 'touched.tmp').is_file()

def test_use_of_replacer(tmpdir):
    """All commands should be run from `directory`."""
    temp_dir = Path(tmpdir)
    run_action = RunAction(
        options={'shell': 'whatever', 'timeout': 1},
        directory=temp_dir,
        replacer=lambda x: 'echo test',
        context_store={},
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
    )
    _, result = run_action.execute(default_timeout=10000)
    assert result == ''

    run_action = RunAction(
        options={'shell': 'sleep 0.1 && echo hi', 'timeout': 0.2},
        directory=temp_dir,
        replacer=lambda x: x,
        context_store={},
    )
    _, result = run_action.execute(default_timeout=0)
    assert result == 'hi'

def test_run_timeout_specified_in_execute(tmpdir):
    """
    Run actions can time out.

    The the option `timeout` is not specified, use `default_timeout` argument
    instead.
    """
    temp_dir = Path(tmpdir)
    run_action = RunAction(
        options={'shell': 'sleep 0.1 && echo hi'},
        directory=temp_dir,
        replacer=lambda x: x,
        context_store={},
    )
    _, result = run_action.execute(default_timeout=0.05)
    assert result == ''

    run_action = RunAction(
        options={'shell': 'sleep 0.1 && echo hi'},
        directory=temp_dir,
        replacer=lambda x: x,
        context_store={},
    )
    _, result = run_action.execute(default_timeout=0.2)
    assert result == 'hi'
