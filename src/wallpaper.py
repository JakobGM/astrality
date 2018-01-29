import logging
import os
import subprocess
from configparser import ConfigParser, ExtendedInterpolation
from pathlib import Path
from typing import Any, Dict

from resolver import Resolver
import timer

logger = logging.getLogger('astrality')
FONT_CATEGORIES = ('primary', 'secondary',)


def import_colors(config: Resolver):
    # TODO: Everything

    wallpaper_theme_directory = config['_runtime']['config_directory'] / 'wallpaper_themes' / 'default'
    color_config_parser = ConfigParser(interpolation=ExtendedInterpolation())
    color_config_path = Path(wallpaper_theme_directory, 'colors.conf')
    color_config_parser.read(color_config_path)
    logger.info(f'Using color config from "{color_config_path}"')

    colors: Dict[str, Dict[str, str]] = {}
    for color_category in color_config_parser.keys():
        if color_category == 'DEFAULT':
            continue
        colors[color_category] = {}
        # TODO
        for period in timer.Solar.periods:
            colors[color_category][period] = color_config_parser[color_category][period]

    logger.debug('Using the following color theme:')
    logger.debug(str(colors))
    return {'colors': colors}
