"""Module for enforcing module 'requires' statements."""

import os
import shutil
from typing import Union
from pathlib import Path

from mypy_extensions import TypedDict

from astrality import utils


class RequirementDict(TypedDict, total=False):
    """Available keys in requirement dictionary."""

    shell: str
    timeout: Union[int, float]
    env: str
    installed: str


class Requirement:
    """
    Class for determining if module dependencies are satisfied.

    Object is truthy if requirements are satisfied.

    :param requirements: Dictionary containing requirements.
    :param directory: Module directory.
    :param timeout: Default timeout for shell commands.
    """

    successful: bool

    def __init__(
        self,
        requirements: RequirementDict,
        directory: Path,
        timeout: Union[int, float] = 1,
    ) -> None:
        """Construct RequirementStatement object."""
        self.successful: bool = True
        self.repr: str = ''

        # Check shell requirements
        if 'shell' in requirements:
            command = requirements['shell']
            result = utils.run_shell(
                command=command,
                fallback=False,
                timeout=requirements.get('timeout') or timeout,
                working_directory=directory,
            )
            if result is False:
                self.repr = f'Unsuccessful command: "{command}", '
                self.successful = False
            else:
                self.repr = f'Sucessful command: "{command}" (OK), '

        # Check environment requirements
        if 'env' in requirements:
            env_variable = requirements['env']
            if env_variable not in os.environ:
                self.repr += f'Missing environment variable: "{env_variable}", '
                self.successful = False
            else:
                self.repr += 'Found environment variable: ' \
                             f'"{env_variable}" (OK), '

        # Check installed requirements
        if 'installed' in requirements:
            program = requirements['installed']
            in_path = bool(shutil.which(program))
            if not in_path:
                self.repr += f'Program not installed: "{program}", '
                self.successful = False
            else:
                self.repr += f'Program installed: "{program}" (OK), '

    def __bool__(self) -> bool:
        """Return True if all requirements are satisfied."""
        return self.successful

    def __repr__(self) -> str:
        """Return string representation of requirement object."""
        self.repr = self.repr if self.repr else 'No requirements (OK), '
        return 'Module requirements: ' + self.repr
