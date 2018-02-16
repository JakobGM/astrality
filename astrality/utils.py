"""General utility functions which are used across the application."""

import logging
import subprocess
from pathlib import Path
from typing import Any, Union

logger = logging.getLogger('astrality')


def run_shell(
    command: str,
    timeout: Union[int, float] = 2,
    fallback: Any = '',
    working_directory: Path = Path.home(),
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
        process.wait(timeout=timeout)

        for error_line in process.stderr:
            logger.error(str(error_line))

        if process.returncode != 0:
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
