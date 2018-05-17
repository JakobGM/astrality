"""Module which keeps track of module setup block actions and created files."""

import hashlib
import logging
import os
from enum import Enum
from pathlib import Path
from typing import Dict, Iterable, List

from mypy_extensions import TypedDict

from astrality import actions, utils
from astrality.xdg import XDG


class CreationMethod(Enum):
    """Ways modules can create files."""
    COMPILE = 'compiled'
    COPY = 'copied'
    SYMLINK = 'symlinked'


class CreationInfo(TypedDict):
    """Information stored for each module created file."""
    # Source file used to create file
    content: str

    # Method used to create file
    method: str

    # Last modification MD5 hash of created file
    hash: str


# Contents of $XDG_DATA_HOME/astrality/created_files.yml.
# Example: {'module_name': {'/created/file': {...}, '/another/file': {...}}}
CreationsYAML = Dict[str, Dict[str, CreationInfo]]


class CreatedFiles:
    """Object which persists which files that have been created by modules."""

    # Dictionary read from created_files.yml containing files created by modules
    creations: CreationsYAML

    # Path to file containing module created files
    _path: Path

    def __init__(self) -> None:
        """Constuct CreatedFiles object."""
        self.creations = utils.load_yaml(path=self.path)

    @property
    def path(self) -> Path:
        """Return path to file which stores files created by modules."""
        if hasattr(self, '_path'):
            return self._path

        xdg = XDG('astrality')
        self._path = xdg.data(resource='created_files.yml')
        if os.stat(self._path).st_size == 0:
            self._path.touch()
            utils.dump_yaml(data={}, path=self._path)

        return self._path

    def insert(
        self,
        module: str,
        creation_method: CreationMethod,
        contents: Iterable[Path],
        targets: Iterable[Path],
    ) -> None:
        """
        Insert files created by a module.

        :param module: Name of module which has created the files.
        :param creation_method: Type of action which has created the file.
        :param contents: The source files used in creating the files.
        :param targets: The files that have be created.
        """
        # We do not want to insert empty sections, to reduce reduntant clutter
        if not contents:
            return

        module_section = self.creations.setdefault(module, {})
        original = module_section.copy()

        for content, target in zip(contents, targets):
            # Do not insert files that actually do not exist
            if not target.exists():
                continue

            creation = module_section.setdefault(
                str(target),
                {},  # type: ignore
            )
            if creation.get('content') != str(content):
                creation['content'] = str(content)
                creation['method'] = creation_method.value
                creation['hash'] = hashlib.md5(target.read_bytes()).hexdigest()

        if module_section != original:
            utils.dump_yaml(data=self.creations, path=self.path)

    def by(self, module) -> List[Path]:
        """
        Return files created by module.

        :param module: Name of module.
        :return: List of paths to created files.
        """
        return [
            Path(creation)
            for creation
            in self.creations.get(module, {}).keys()
        ]

    def cleanup(self, module: str, dry_run: bool = False) -> None:
        """
        Delete files created by module.

        :param module: Name of module, file creation of which will be deleted.
        :param dry_run: If True, no files will be deleted, only logging will
            occur.
        """
        logger = logging.getLogger(__name__)
        module_creations = self.creations.get(module, {})
        for creation, info in module_creations.items():
            creation_method = info['method']
            content = info['content']
            log_msg = (
                f'[Cleanup] Deleting "{creation}" '
                f'({creation_method} content from "{content}")'
            )
            if dry_run:
                logger.info('SKIPPED: ' + log_msg)
                continue

            creation_path = Path(creation)
            if creation_path.exists():
                logger.info(log_msg)
                creation_path.unlink()
            else:
                logger.info(log_msg + ' [No longer exists!]')

        if not dry_run:
            self.creations.pop(module, None)
            utils.dump_yaml(data=self.creations, path=self.path)

    def __repr__(self) -> str:
        """Return string representation of CreatedFiles object."""
        return f'CreatedFiles(path={self.path})'


class ExecutedActions:
    """
    Object which persists executed module actions.

    :param module_name: Unique string id of module.
    """

    # Path to file containing executed setup actions
    _path: Path

    def __init__(self, module_name: str) -> None:
        """Construct ExecutedActions object."""
        self.module = module_name
        self.new_actions = {}  # type: ignore

        file_data = utils.load_yaml(path=self.path)
        self.old_actions = file_data.setdefault(
            self.module,
            {},
        )

    def is_new(
        self,
        action_type: str,
        action_options,
    ) -> bool:
        """
        Return True if the specified action has not been executed earlier.

        :param action_type: Type of action, see ActionBlock.action_types.
        :param action_options: Configuration of action to be performed.
        """
        assert action_type in actions.ActionBlock.action_types
        if not action_options:
            # Empty actions can be disregarded.
            return False

        is_new = action_options not in self.old_actions.get(
            action_type,
            [],
        ) and action_options not in self.new_actions.get(
            action_type,
            [],
        )

        if is_new:
            self.new_actions                 \
                .setdefault(action_type, []) \
                .append(action_options)

        return is_new

    def write(self) -> None:
        """Persist all actions that have been checked in object lifetime."""
        if not self.new_actions:
            return

        file_data = utils.load_yaml(path=self.path)
        file_data.setdefault(self.module, {})

        for action_type, action_options in self.new_actions.items():
            file_data[self.module].setdefault(
                action_type,
                [],
            ).extend(action_options)

        utils.dump_yaml(
            path=self.path,
            data=file_data,
        )

    def reset(self) -> None:
        """Delete all executed module actions."""
        file_data = utils.load_yaml(path=self.path)
        reset_actions = file_data.pop(self.module, None)

        logger = logging.getLogger(__name__)
        if not reset_actions:
            logger.error(
                'No saved executed on_setup actions for module '
                f'"{self.module}"!',
            )
        else:
            logger.info(
                f'Reset the following actions for module "{self.module}":\n' +
                utils.yaml_str({self.module: reset_actions}),
            )

        utils.dump_yaml(
            path=self.path,
            data=file_data,
        )
        self.old_actions = {}

    @property
    def path(self) -> Path:
        """Return path to file which stores executed module setup actions."""
        if hasattr(self, '_path'):
            return self._path

        xdg = XDG('astrality')
        self._path = xdg.data(resource='setup.yml')
        if os.stat(self._path).st_size == 0:
            self._path.touch()
            utils.dump_yaml(data={}, path=self._path)

        return self._path

    def __repr__(self) -> str:
        """Return string representation of ExecutedActions object."""
        return f'ExecutedActions(module_name={self.module}, path={self.path})'
