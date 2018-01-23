"""Specifies everything related to application spanning configuration."""

import os
from configparser import ConfigParser, ExtendedInterpolation
from math import inf
from pathlib import Path
from typing import Any, Optional, Tuple, Union

from conky import create_conky_temp_files
from timer import TIMERS
from wallpaper import import_colors, wallpaper_paths


class Config:
    """
    Dictionary-like object which specifies application configuration options.

    It also tries resolves access to integer indexed keys if a lesser integer
    key exists. These integer keys are still represented as strings.

    An example of its functionality:
    replacements = Resolver({
    'colors': {'1': 'CACCFD', '2': 'BACBEB'}
    })
    replacements['1']
    >>> 'CACCFD'
    replacements['2']
    >>> 'BACBEB'
    replacements['3']
    >>> 'BACBEB'
    """

    def __init__(
        self,
        config: Optional[Union[ConfigParser, dict]] = None,
    ) -> None:
        """
        Initialize a configuration file from source object.

        The source object can either be a ConfigParser object which has already
        .read() a configuration file, a dictionary, or if not given an
        argument, an empty Config object is initialized.
        """

        if isinstance(config, (ConfigParser, dict,)):
            self.update(config)
        elif config is not None:
            raise ValueError('Config initialized with wrong argument type.')

        # Determine the greatest "string integer" index inserted
        self._max_key = -inf
        if hasattr(self, '_dict'):
            for key in self._dict.keys():
                try:
                    self._max_key = max(int(key), self._max_key)
                except ValueError:
                    pass

    def __eq__(self, other) -> bool:
        """Check if config is identical to other config or dictionary."""

        if hasattr(self, '_dict'):
            return self._dict.__eq__(other)
        else:
            return {}.__eq__(other)

    def __req__(self, other) -> bool:
        """Right side comparison, see self.__eq__()."""
        return self.__eq__(other)

    def __setitem__(self, key: str, value: str) -> None:
        """Insert `value` into the `key` index."""
        if not hasattr(self, '_dict'):
            self._dict = {}

        try:
            self._max_key = max(int(key), self._max_key)
        except ValueError as e:
            if 'invalid literal for int() with base 10' in str(e):
                pass
            else:
                raise

        if isinstance(value, dict):
            self._dict[key] = Config(value)
        else:
            self._dict[key] = value

    def __getitem__(self, key: Any) -> Any:
        """
        Get item inserted into `key` index, with integer index resolution.

        Here "integer index resolution" means that if you try to retrieve
        non-existent "string integer" index '2', it will retrieve the greatest
        "string integer" available instead.
        """
        if not hasattr(self, '_dict'):
            raise KeyError('Tried to access key from empty config section')

        try:
            # Return excact hit if present
            return self._dict[key]

        except KeyError as key_error:
            # The key is not present. See if we can resolve the use of another
            # one through integer key priority
            if self._max_key > -inf:
                # Another integer key has been inserted earlier
                try:
                    int(key)
                    # We can return the max integer key previously inserted
                    return self._dict[str(self._max_key)]

                except ValueError as value_error:
                    if 'invalid literal for int() with base 10' in str(value_error):
                        # The key is not representable as an integer, so we
                        # have a normal KeyError exception on our hands. Raise
                        # the originally caught KeyError again.
                        raise key_error
                    else:
                        # Throwing any other ValueErrors just in case
                        raise
            else:
                raise KeyError(f'Integer index "{key}" is non-existent and had '
                               'no lower index to be substituted for')


    def get(self, key, defualt=None) -> Any:
        """Get value from index with fallback value `default`."""
        try:
            return self.__getitem__(key)
        except KeyError:
            return defualt

    def __repr__(self) -> str:
        """Return human-readable representation of Config object."""
        if hasattr(self, '_dict'):
            return self._dict.__repr__()
        else:
            return {}.__repr__()

    def __str__(self) -> str:
        """Return string representation of Config object."""
        if hasattr(self, '_dict'):
            return self._dict.__str__()
        else:
            return {}.__str__()

    def items(self):
        if hasattr(self, '_dict'):
            return self._dict.items()
        else:
            return {}.items()

    def keys(self) -> Tuple[str]:
        """Return all keys which have been inserted into the Config object."""
        if hasattr(self, '_dict'):
            return self._dict.keys()
        else:
            return {}.keys()

    def values(self):
        """Return all values inserted into the Config object."""
        if hasattr(self, '_dict'):
            return self._dict.values()
        else:
            return {}.values()

    def update(self, other: Union[ConfigParser, dict]) -> None:
        """Overwrite all items from other onto the Config object."""

        if isinstance(other, ConfigParser):
            # Populate internal data structure from ConfigParser object
            if not hasattr(self, '_dict'):
                self._dict = {}

            for section_name, section in other.items():
                self._dict[section_name] = Config()
                for key, value in section.items():
                    self._dict[section_name][key] = value

        elif isinstance(other, (ConfigParser, dict,)):
            # Populate internal data structure from dictionary
            if not hasattr(self, '_dict'):
                self._dict = Config()

            for key, value in other.items():
                self._dict[key] = value

        else:
            raise NotImplementedError(
                f'Config.update() not yet implemented for type {type(other)})'
            )


def infer_config_location(
    config_directory: Optional[str] = None,
) -> Tuple[str, str]:
    """
    Try to find the configuration directory for solarity, based on filesystem
    or specific environment variables if they are present several places to put
    it. See README.md.
    """
    if not config_directory:
        if 'SOLARITY_CONFIG_HOME' in os.environ:
            # The user has set a custom config directory for solarity
            config_directory = os.environ['SOLARITY_CONFIG_HOME']
        else:
            # Follow the XDG directory standard
            config_directory = os.path.join(
                os.getenv('XDG_CONFIG_HOME', '~/.config'),
                'solarity',
            )

    config_file = os.path.join(config_directory, 'solarity.conf')

    if not os.path.isfile(config_file):
        print(
            'Configuration file not found in its expected path '
            + config_file +
            '.'
        )
        config_directory = str(Path(__file__).parents[1])
        config_file = os.path.join(config_directory, 'solarity.conf.example')
        print(f'Using example configuration instead: "{config_file}"')
    else:
        print(f'Using configuration file "{config_file}"')

    return config_directory, config_file


def populate_config_from_file(
    config_directory: Optional[str] = None,
    config: Config = Config(),
) -> Config:
    config_directory, config_file = infer_config_location(config_directory)

    # Populate the config dictionary with items from the `solarity.conf`
    # configuration file
    config_parser = ConfigParser(interpolation=ExtendedInterpolation())
    config_parser.read(config_file)
    config.update(config_parser)

    # Insert infered paths from config_directory
    config_module_paths = {
        module: os.path.join(config_directory, 'conky_themes', module)
        for module
        in config_parser['conky']['modules'].split()
    }

    conky_module_templates = {
        module: os.path.join(path, 'template.conf')
        for module, path
        in config_module_paths.items()
    }

    wallpaper_theme_directory = os.path.join(
        config_directory,
        'wallpaper_themes',
        config['wallpaper']['theme'],
    )

    config.update({
        'config_directory': config_directory,
        'config_file': config_file,
        'conky_module_paths': config_module_paths,
        'conky_module_templates': conky_module_templates,
        'wallpaper_theme_directory': wallpaper_theme_directory,
    })

    return config

def user_configuration(config_directory: Optional[str] = None) -> Config:
    """
    Create a configuration dictionary which should directly reflect the
    hierarchy of a typical `solarity.conf` file. Users should be able to insert
    elements from their configuration directly into conky module templates. The
    mapping should be:

    ${solarity:conky:main_font} -> config['conky']['main_font']

    Some additional configurations are automatically added to the root level of
    the dictionary such as:
    - config['config_directory']
    - config['config_file']
    - config['conky_module_paths']
    """
    config = populate_config_from_file(config_directory)
    config['timer_class'] = TIMERS[config['timer']['type']]
    config['periods'] = config['timer_class'].periods

    # Find wallpaper paths corresponding to the wallpaper theme set by the user
    config['wallpaper_paths'] = wallpaper_paths(config=config)

    # Import the colorscheme specified by the users wallpaper theme
    config['colors'] = import_colors(config)

    # Create temporary conky files used by conky, but files are overwritten
    # when the time of day changes
    config['conky_temp_files'] = create_conky_temp_files(config)

    from pprint import pprint; pprint(config)
    return config
