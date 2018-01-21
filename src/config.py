from configparser import ConfigParser, ExtendedInterpolation
import os
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from conky import create_conky_temp_files
from timer import Solar
from wallpaper import import_colors, wallpaper_paths

Config = Dict['str', Any]


def infer_config_location(
    config_directory: Optional[str] = None,
) -> Tuple[str, str]:
    """
    Try to find the configuration directory for solarity, based on filesystem
    or specific environment variables if they are present several places to put
    it. See README.md
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
            'Configuration file not found in its expected path ' \
            f'"{config_file}".'
        )
        config_directory = str(Path(__file__).parents[1])
        config_file = os.path.join(config_directory, 'solarity.conf.example')
        print(f'Using example configuration instead: "{config_file}"')
    else:
        print(f'Using configuration file "{config_file}"')

    return config_directory, config_file


def populate_config_from_file(config_directory: Optional[str] = None, config: Config = {}) -> Config:
    config_directory, config_file = infer_config_location(config_directory)

    # Populate the config dictionary with items from the `solarity.conf`
    # configuration file
    config_parser = ConfigParser(interpolation=ExtendedInterpolation())
    config_parser.read(config_file)
    for category, items in config_parser.items():
        config[category] = dict(items)

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
    config['periods'] = Solar.periods

    # Find wallpaper paths corresponding to the wallpaper theme set by the user
    config['wallpaper_paths'] = wallpaper_paths(config=config)

    # Import the colorscheme specified by the users wallpaper theme
    config['colors'] = import_colors(config)

    # Create temporary conky files used by conky, but files are overwritten
    # when the time of day changes
    config['conky_temp_files'] = create_conky_temp_files(config)

    return config
