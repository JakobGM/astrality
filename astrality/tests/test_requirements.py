"""Tests for requirements module."""

from pathlib import Path

from astrality.requirements import Requirement

def test_null_object_pattern():
    """Empty requirements should be considered satisfied."""
    successful_shell_requirement = Requirement(
        requirements={},
        directory=Path('/'),
    )
    assert successful_shell_requirement

def test_shell_command_requirement():
    """Requirement should be truthy when command returns 0 exit code."""
    successful_shell_requirement = Requirement(
        requirements={'shell': 'command -v ls'},
        directory=Path('/'),
    )
    assert successful_shell_requirement

    unsuccessful_shell_requirement = Requirement(
        requirements={'shell': 'command -v does_not_exist'},
        directory=Path('/'),
    )
    assert not unsuccessful_shell_requirement

def test_that_shell_commands_are_run_in_correct_diretory():
    """All shell commands should be run from 'directory'"""
    successful_shell_requirement = Requirement(
        requirements={'shell': 'ls tmp'},
        directory=Path('/'),
    )
    assert successful_shell_requirement

    unsuccessful_shell_requirement = Requirement(
        requirements={'shell': 'ls does_not_exist'},
        directory=Path('/'),
    )
    assert not unsuccessful_shell_requirement

def test_shell_command_timeout():
    """Shell commands can time out."""
    default_times_out = Requirement(
        requirements={'shell': 'sleep 0.1'},
        directory=Path('/'),
        timeout=0.01,
    )
    assert not default_times_out

    default_does_not_timeout = Requirement(
        requirements={'shell': 'sleep 0.1'},
        directory=Path('/'),
        timeout=0.2,
    )
    assert default_does_not_timeout

    specifed_does_not_timeout = Requirement(
        requirements={'shell': 'sleep 0.1', 'timeout': 0.2},
        directory=Path('/'),
        timeout=0.5,
    )
    assert specifed_does_not_timeout

    specified_does_timeout = Requirement(
        requirements={'shell': 'sleep 0.1', 'timeout': 0.05},
        directory=Path('/'),
        timeout=1000,
    )
    assert not specified_does_timeout

def test_environment_variable_requirement():
    """Requirement should be truthy when environment variable is available."""
    successful_env_requirement = Requirement(
        requirements={'env': 'EXAMPLE_ENV_VARIABLE'},
        directory=Path('/'),
    )
    assert successful_env_requirement

    unsuccessful_env_requirement = Requirement(
        requirements={'env': 'THIS_IS_NOT_SET'},
        directory=Path('/'),
    )
    assert not unsuccessful_env_requirement

def test_installed_requirement():
    """Requirement should be truthy when value is in $PATH."""
    successful_installed_requirement = Requirement(
        requirements={'installed': 'ls'},
        directory=Path('/'),
    )
    assert successful_installed_requirement

    unsuccessful_installed_requirement = Requirement(
        requirements={'installed': 'does_not_exist'},
        directory=Path('/'),
    )
    assert not unsuccessful_installed_requirement
