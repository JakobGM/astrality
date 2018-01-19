from configparser import ConfigParser
import os
from typing import Any, Dict, Optional

from astral import Location
from tzlocal import get_localzone

from time_of_day import PERIODS

Config = Dict['str', Any]


def user_configuration(config_directory_path: Optional[str] = None) -> Config:
    if config_directory_path:
        config_dir = config_directory_path
    else:
        config_dir = os.getenv('XDG_CONFIG_HOME', '~/.config') + '/solarity'

    config_file = config_dir + '/solarity.conf'

    print(f'Using configuration file "{config_file}"')

    config_parser = ConfigParser()
    config_parser.read(config_file)

    config_module_paths = {
        module: config_dir + '/conky_themes/' + module
        for module
        in config_parser['appearance']['conky-modules'].split()
    }

    config = {
        'config_directory': config_dir,
        'config_file': config_file,
        'conky_module_paths': config_module_paths,
        'longitude': config_parser['location']['longitude'],
        'latitude': config_parser['location']['latitude'],
        'elevation': config_parser['location']['elevation'],
        'wallpaper_theme': config_parser['appearance']['wallpaper-theme'],
        'refresh_period': int(
            config_parser['behaviour'].get('refresh-period', '60')
        ),
    }

    config['location'] = astral_location(config)
    config['wallpaper_paths'] = wallpaper_paths(config)

    return config


def astral_location(config: Config) -> Location:
    # Initialize a custom location for astral, as it doesn't necessarily include
    # your current city of residence
    location = Location()

    # These two doesn't really matter
    location.name = 'CityNotImportant'
    location.region = 'RegionIsNotImportantEither'

    # But these are important, and should be provided by the user
    location.latitude = float(config['latitude'])
    location.longitude = float(config['longitude'])
    location.elevation = float(config['elevation'])

    # We can get the timezone from the system
    location.timezone = str(get_localzone())

    return location


def wallpaper_paths(config: Config) -> Dict[str, str]:
    wallpaper_theme = config['wallpaper_theme']
    config_dir = config['config_directory']
    wallpaper_directory = config_dir + '/wallpaper_themes/' + wallpaper_theme

    paths = {
        period: wallpaper_directory + '/' + period + '.jpg'
        for period
        in PERIODS
    }
    return paths
