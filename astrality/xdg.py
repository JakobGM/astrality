"""Module implementing XDG directory standard for astrality."""

import os
from pathlib import Path


class XDG:
    """
    Class for handling the XDG directory standard.

    :param application_name: Name of application to use XDG directory standard.
    """

    def __init__(self, application_name: str = 'astrality') -> None:
        """Contstruct XDG object for application."""
        self.application_name = application_name
        self.XDG_DATA_HOME = Path(os.environ.get(
            'XDG_DATA_HOME',
            '~/.local/share',
        )).expanduser()
        self.XDG_CONFIG_HOME = Path(os.environ.get(
            'XDG_CONFIG_HOME',
            '~/.config',
        )).expanduser()

    @property
    def data_home(self) -> Path:
        """
        Return XDG_DATA_HOME directory of application.

        :return: Path to resolved value of XDG_DATA_HOME.
        """
        application_data_home = self.XDG_DATA_HOME / self.application_name
        application_data_home.mkdir(parents=True, exist_ok=True)
        return application_data_home

    def data(self, resource: str) -> Path:
        """
        Return file resource of application.

        :param resource: Relative string path, i.e. $XDG_DATA_HOME/<resource>.
        :return: Path to touched data resource.
        """
        resource_path = self.data_home / resource
        resource_path.parent.mkdir(parents=True, exist_ok=True)
        resource_path.touch(exist_ok=True)
        return resource_path
