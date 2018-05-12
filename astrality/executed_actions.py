"""Module which keeps track of module setup block actions."""

import os
from pathlib import Path

from astrality import actions
from astrality.config import expand_path
from astrality import utils


def xdg_data_home(application: str) -> Path:
    """Return XDG directory standard path for application data."""
    xdg_data_home = expand_path(
        path=Path(
            os.environ.get(
                'XDG_DATA_HOME',
                '$HOME/.local/share',
            ),
        ),
        config_directory=Path('/'),
    )
    application_data_home = xdg_data_home / application
    application_data_home.mkdir(exist_ok=True)
    return application_data_home


class ExecutedActions:
    """
    Object which persists executed module actions.

    :param module_name: Unique string id of module.
    """

    # True if we have checked executed() on a new action configuration.
    newly_executed_actions: bool

    def __init__(self, module_name: str) -> None:
        """Construct ExecutedActions object."""
        self.module = module_name
        self.file_data = utils.load_yaml(path=self.path)
        self.executed_actions = self.file_data.setdefault(
            self.module,
            {},
        )
        self.newly_executed_actions = False

    def executed(
        self,
        action_type: str,
        action_options,
    ) -> bool:
        """
        Return True if action config of action type has been saved earlier.

        :param action_type: Type of action, see ActionBlock.action_types.
        :param action_options: Configuration of action to be performed.
        """
        assert action_type in actions.ActionBlock.action_types
        if not action_options:
            # Empty actions can be disregarded.
            return False

        has_been_executed = action_options in self.executed_actions.get(
            action_type,
            [],
        )

        if not has_been_executed:
            self.executed_actions            \
                .setdefault(action_type, []) \
                .append(action_options)
            self.newly_executed_actions = True

        return has_been_executed

    def save_checked_actions(self) -> None:
        """Persist all actions that have been checked in object lifetime."""
        if not self.newly_executed_actions:
            return

        file_data = utils.load_yaml(path=self.path)
        file_data[self.module] = self.executed_actions
        utils.dump_yaml(
            path=self.path,
            data=file_data,
        )

    @property
    def path(self) -> Path:
        """Return path to file which stores executed module setup actions."""
        if hasattr(self, '_path'):
            return self._path

        self._path: Path = xdg_data_home('astrality') / 'setup.yml'
        if not self._path.exists():
            self._path.touch()
            utils.dump_yaml(data={}, path=self._path)

        return self._path

    def __repr__(self) -> str:
        """Return string representation of ExecutedActions object."""
        return f'ExecutedActions(module_name={self.module}, path={self.path})'
