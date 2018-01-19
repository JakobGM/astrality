from configparser import ConfigParser
import os
from typing import Any, Dict, Optional

from astral import Location
from tzlocal import get_localzone

from time_of_day import PERIODS

Config = Dict['str', Any]


def user_configuration(config_directory_path: Optional[str] = None) -> Config:
    """
    Creates a configuration dictionary which should directly reflect the
    hierarchy of a typical `solarity.conf` file. Users should be able to insert
    elements from their configuration directly into conky module templates. The
    mapping should be:

    ${solarity:conky:main-font} -> config['conky']['main-font']

    Some additional configurations are automatically added to the root level of
    the dictionary such as:
    - config['config-dir']
    - config['config-file']
    - config['conky-module-paths']
    """
    # Determine configuration files
    if config_directory_path:
        # The testing framework might inject its own config file, or the user
        # has specified $SOLARITY_CONFIG_HOME environment variable, which has
        # been injected by main.py
        config_dir = config_directory_path
    else:
        # Follow the XDG directory standard
        config_dir = os.getenv('XDG_CONFIG_HOME', '~/.config') + '/solarity'

    config_file = config_dir + '/solarity.conf'
    print(f'Using configuration file "{config_file}"')

    # Populate the config dictionary with items from the `solarity.conf`
    # configuration file
    config_parser = ConfigParser()
    config_parser.read(config_file)
    config = {
        category: dict(items)
        for category, items
        in config_parser.items()
    }

    # Insert infered paths from config_dir
    config_module_paths = {
        module: config_dir + '/conky_themes/' + module
        for module
        in config_parser['conky']['modules'].split()
    }

    config.update({
        'config-directory': config_dir,
        'config-file': config_file,
        'conky-module-paths': config_module_paths,
    })

    # Populate rest of config based on a partially filled config
    config['location']['astral'] = astral_location(
        latitude=float(config['location']['latitude']),
        longitude=float(config['location']['longitude']),
        elevation=float(config['location']['elevation']),
    )

    config['wallpaper-paths'] = wallpaper_paths(
        config_path=config['config-directory'],
        wallpaper_theme=config['wallpaper']['theme'],
    )


    return config


def astral_location(
    latitude: float,
    longitude: float,
    elevation: float,
) -> Location:
    # Initialize a custom location for astral, as it doesn't necessarily include
    # your current city of residence
    location = Location()

    # These two doesn't really matter
    location.name = 'CityNotImportant'
    location.region = 'RegionIsNotImportantEither'

    # But these are important, and should be provided by the user
    location.latitude = latitude
    location.longitude = longitude
    location.elevation = elevation

    # We can get the timezone from the system
    location.timezone = str(get_localzone())

    return location


def wallpaper_paths(
    config_path: str,
    wallpaper_theme: str,
) -> Dict[str, str]:
    """
    Given the configuration directory and wallpaper theme, this function
    returns a dictionary containing:

    {..., 'period': 'full_wallpaper_path', ...}

    """
    wallpaper_directory = config_path + '/wallpaper_themes/' + wallpaper_theme

    paths = {
        period: wallpaper_directory + '/' + period + '.jpg'
        for period
        in PERIODS
    }
    return paths
