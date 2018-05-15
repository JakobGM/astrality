"""Module which keeps track of module setup block actions."""

import os
from pathlib import Path
import logging

from astrality import actions
from astrality import utils
from astrality.xdg import XDG


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
