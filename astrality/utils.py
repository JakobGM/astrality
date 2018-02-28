"""General utility functions which are used across the application."""

import logging
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, Union

logger = logging.getLogger('astrality')


def run_shell(
    command: str,
    timeout: Union[int, float] = 2,
    fallback: Any = '',
    working_directory: Path = Path.home(),
    allow_error_codes: bool = False,
) -> str:
    """
    Return the standard output of a shell command.

    If the shell command has a non-zero exit code or times out, the function
    returns the `fallback` argument instead of the standard output.
    """

    process = subprocess.Popen(
        command,
        cwd=working_directory,
        shell=True,
        universal_newlines=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        # We add just a small extra wait in case users specify 0 seconds,
        # in order to not print an error when a command is really quick.
        if timeout == 0:
            process.wait(timeout=timeout + 0.1)
        else:
            process.wait(timeout=timeout)

        for error_line in process.stderr:
            logger.error(str(error_line))

        if process.returncode != 0 and not allow_error_codes:
            logger.error(
                f'Command "{command}" exited with non-zero return code: ' +
                str(process.returncode)
            )
            return fallback
        else:
            stdout = process.communicate()[0]
            logger.info(stdout)
            return stdout.replace('\n', '')

    except subprocess.TimeoutExpired:
        logger.warning(
            f'The command "{command}" used more than {timeout} seconds in '
            'order to finish. The exit code can not be verified. This might be '
            'intentional for background processes and daemons.'
        )
        return fallback


def generate_expanded_env_dict() -> Dict[str, str]:
    """Return os.environ dict with all env variables expanded."""

    env_dict = {}
    for name, value in os.environ.items():
        try:
            env_dict[name] = os.path.expandvars(value)
        except ValueError as e:
            if 'invalid interpolation syntax' in str(e):
                logger.warning(f'''
                Could not use environment variable {name}={value}.
                It is too complex for expansion, using unexpanded value
                instead...
                ''')
                env_dict[name] = value
            else:
                raise

    return env_dict


