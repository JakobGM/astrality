from configparser import ConfigParser, ExtendedInterpolation
import os
from typing import Any, Dict, Optional

from astral import Location
from tzlocal import get_localzone

from conky import create_conky_temp_files
from time_of_day import PERIODS

Config = Dict['str', Any]
FONT_CATEGORIES = ('primary', 'secondary',)


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
    # Determine configuration folder path
    config_directory_path=os.environ.get('SOLARITY_CONFIG_HOME', None)

    if config_directory_path:
        # The testing framework might inject its own config file, or the user
        # has specified $SOLARITY_CONFIG_HOME environment variable, which has
        # been injected by main.py
        config_dir = config_directory_path
    else:
        # Follow the XDG directory standard
        config_dir = os.getenv('XDG_CONFIG_HOME', '~/.config') + '/solarity'

    config_file = config_dir + '/solarity.conf'

    if not os.path.isfile(config_file):
        raise RuntimeError(
            'Configuration file not found in its expected path ' \
            f'"{config_file}".'
        )
    else:
        print(f'Using configuration file "{config_file}"')

    # Populate the config dictionary with items from the `solarity.conf`
    # configuration file
    config_parser = ConfigParser(interpolation=ExtendedInterpolation())
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

    conky_module_templates = {
        module: path + '/template.conf'
        for module, path
        in config_module_paths.items()
    }

    config.update({
        'config-directory': config_dir,
        'config-file': config_file,
        'conky-module-paths': config_module_paths,
        'conky-module-templates': conky_module_templates,
        'wallpaper-theme-directory': \
            config_dir + '/wallpaper_themes/' + config['wallpaper']['theme'],
    })

    # Populate rest of config based on a partially filled config
    # Initialize astral Location() object from user configuration
    config['location']['astral'] = astral_location(
        latitude=float(config['location']['latitude']),
        longitude=float(config['location']['longitude']),
        elevation=float(config['location']['elevation']),
        config=config,
    )

    # Find wallpaper paths corresponding to the wallpaper theme set by the user
    config['wallpaper-paths'] = wallpaper_paths(
        config_path=config['config-directory'],
        wallpaper_theme=config['wallpaper']['theme'],
    )

    # Import the colorscheme specified by the users wallpaper theme
    config['colors'] = import_colors(config['wallpaper-theme-directory'])

    # Create temporary conky files used by conky, but files are overwritten
    # when the time of day changes
    config['conky-temp-files'] = create_conky_temp_files(config)

    return config


def astral_location(
    latitude: float,
    longitude: float,
    elevation: float,
    config: Config,
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

    if 'timezone' in config['location']:
        timezone = config['location']['timezone']
        print(f'You have manually set your timezone to "{timezone}"')
        location.timezone = timezone
    else:
        timezone = str(get_localzone())
        print(f'Your timezone is inferred to be "{timezone}"')
        location.timezone = timezone

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
        period: wallpaper_directory + '/' + period
        for period
        in PERIODS
    }
    return paths

def import_colors(wallpaper_theme_directory: str):
    color_config_parser = ConfigParser(interpolation=ExtendedInterpolation())
    color_config_path = wallpaper_theme_directory + '/colors.conf'
    color_config_parser.read(color_config_path)
    print(f'Using color config from "{color_config_path}"')

    colors = {}
    for color_category in FONT_CATEGORIES:
        colors[color_category] = {}
        for period in PERIODS:
            colors[color_category][period] = color_config_parser[color_category][period]

    return colors
