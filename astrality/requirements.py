"""Module for enforcing module 'requires' statements."""

import logging
import os
import shutil
from pathlib import Path
from typing import Union, Dict, TYPE_CHECKING, Iterable

from mypy_extensions import TypedDict

from astrality import utils


if TYPE_CHECKING:
    from astrality.module import Module  # noqa


class RequirementDict(TypedDict, total=False):
    """Available keys in requirement dictionary."""

    shell: str
    timeout: Union[int, float]
    env: str
    installed: str
    module: str


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

    @staticmethod
    def pop_missing_module_dependencies(
        modules: Dict[str, 'Module'],
    ) -> Dict[str, 'Module']:
        """
        Pop modules which miss their module dependencies.

        :param modules: Dictionary containing modules.
        :return: Dictionary with removed modules which miss their module
            dependencies.
        """
        original_length = len(modules)

        for module_name, module in list(modules.items()):
            if not Requirement.satisfied_module_dependencies(
                module=module,
                enabled_modules=tuple(modules.keys()),
            ):
                del modules[module_name]
                continue

        if original_length != len(modules):
            return Requirement.pop_missing_module_dependencies(
                modules=modules,
            )

        return modules

    @staticmethod
    def satisfied_module_dependencies(
        module: 'Module',
        enabled_modules: Iterable[str],
    ) -> bool:
        """
        Return True if all module dependencies of module are enabled.

        :param module: Module to inspect for module dependencies.
        :param enabled_modules: Iterable of enabled module names.
        :return: True if all module dependencies are satisfied.
        """
        for module_dependency in module.depends_on:
            if module_dependency not in enabled_modules:
                logger = logging.getLogger(__name__)
                logger.error(
                    f'[module/{module.name}] Missing module dependency: '
                    f'"{module_dependency}". Disabling module!',
                )
                return False
        else:
            return True

    def __bool__(self) -> bool:
        """Return True if all requirements are satisfied."""
        return self.successful

    def __repr__(self) -> str:
        """Return string representation of requirement object."""
        self.repr = self.repr if self.repr else 'No requirements (OK), '
        return 'Module requirements: ' + self.repr
