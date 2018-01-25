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
    wallpaper_path = config['_runtime']['wallpaper_paths'][period]
    set_feh_wallpaper(wallpaper_path, config)


def import_colors(config: Config):
    wallpaper_theme_directory = config['_runtime']['wallpaper_theme_directory']
    color_config_parser = ConfigParser(interpolation=ExtendedInterpolation())
    color_config_path = Path(wallpaper_theme_directory, 'colors.conf')
    color_config_parser.read(color_config_path)
    print(f'Using color config from "{color_config_path}"')

    colors: Dict[str, Dict[str, str]] = {}
    for color_category in color_config_parser.keys():
        if color_category == 'DEFAULT':
            continue
        colors[color_category] = {}
        for period in config['_runtime']['periods']:
            colors[color_category][period] = color_config_parser[color_category][period]

    print('Using the following color theme:')
    pprint(colors)
    return {'colors': colors}


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

    print('Setting new wallpaper: ' + str(wallpaper_path))
    p = subprocess.Popen([
        'feh',
        feh_option,
        str(wallpaper_path),
    ])
    p.wait()
