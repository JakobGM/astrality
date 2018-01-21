import os
import subprocess
from configparser import ConfigParser, ExtendedInterpolation
from glob import glob
from typing import Any, Dict

Config = Dict['str', Any]
FONT_CATEGORIES = ('primary', 'secondary',)


def update_wallpaper(config: Config, period: str) -> None:
    wallpaper_path = config['wallpaper_paths'][period]
    wallpaper_path = glob(wallpaper_path + '.*')[0]

    print('Setting new wallpaper: ' + wallpaper_path)
    subprocess.Popen([
        'feh',
        config['wallpaper'].get('feh-option', '--bg-scale'),
        wallpaper_path,
    ])

def import_colors(config: Config):
    wallpaper_theme_directory = config['wallpaper_theme_directory']
    color_config_parser = ConfigParser(interpolation=ExtendedInterpolation())
    color_config_path = os.path.join(wallpaper_theme_directory, 'colors.conf')
    color_config_parser.read(color_config_path)
    print(f'Using color config from "{color_config_path}"')

    colors = {}
    for color_category in FONT_CATEGORIES:
        colors[color_category] = {}
        for period in config['periods']:
            colors[color_category][period] = color_config_parser[color_category][period]

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
    this_file = os.path.realpath(__file__)
    parent_dir = os.path.join(*this_file.split('/')[:-1])
    feh_process = subprocess.Popen([
        'feh',
        config['wallpaper'].get('feh-option', '--bg-scale'),
        '/' + parent_dir + '/solid_black_background.jpeg',
    ])
    try:
        exit_code = feh_process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        print('feh is using unusually long time to set the background image.')
    finally:
        if exit_code != 0:
            print(f'feh exited with error code: {exit_code}.')
