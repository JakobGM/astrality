import os
import subprocess
from configparser import ConfigParser, ExtendedInterpolation
from glob import glob
from pathlib import Path
from pprint import pprint
from typing import Any, Dict

Config = Dict['str', Any]
FONT_CATEGORIES = ('primary', 'secondary',)


def update_wallpaper(config: Config, period: str) -> None:
    wallpaper_path = config['wallpaper_paths'][period]
    wallpaper_path = glob(wallpaper_path + '.*')[0]
    set_feh_wallpaper(wallpaper_path, config)


def import_colors(config: Config):
    wallpaper_theme_directory = config['wallpaper_theme_directory']
    color_config_parser = ConfigParser(interpolation=ExtendedInterpolation())
    color_config_path = os.path.join(wallpaper_theme_directory, 'colors.conf')
    color_config_parser.read(color_config_path)
    print(f'Using color config from "{color_config_path}"')

    colors = {}
    for color_category in color_config_parser.keys():
        if color_category == 'DEFAULT':
            continue
        colors[color_category] = {}
        for period in config['periods']:
            colors[color_category][period] = color_config_parser[color_category][period]

    print('Using the following color theme:')
    pprint(colors)
    return colors


def wallpaper_paths(config: Config) -> Dict[str, str]:
    """
    Given the configuration directory and wallpaper theme, this function
    returns a dictionary containing.

    {..., 'period': 'full_wallpaper_path', ...}

    """
    wallpaper_directory = os.path.join(
        config['config_directory'],
        'wallpaper_themes',
        config['wallpaper']['theme']
    )

    paths = {
        period: os.path.join(wallpaper_directory, period)
        for period
        in config['periods']
    }
    return paths


def exit_feh(config) -> None:
    parent_dir = Path(__file__).parent
    fallback_wallpaper_path = os.path.join(
        config['wallpaper'].get('feh_option', '--bg-scale'),
        parent_dir,
        'solid_black_background.jpeg',
    )
    set_feh_wallpaper(fallback_wallpaper_path, config)


def set_feh_wallpaper(wallpaper_path: Path, config: Config) -> None:
    feh_option = config['wallpaper'].get('feh_option', '--bg-scale')

    print('Setting new wallpaper: ' + wallpaper_path)
    p = subprocess.Popen([
        'feh',
        feh_option,
        str(wallpaper_path),
    ])
    p.wait()
