"""Specifies everything related to application spanning configuration."""

import logging
import os
from configparser import ConfigParser, ExtendedInterpolation, InterpolationMissingOptionError
from pathlib import Path
from typing import Dict, Optional, Tuple

from conky import create_conky_temp_files
from timer import TIMERS
from wallpaper import import_colors

from resolver import Resolver

logger = logging.getLogger('astrality')


def infer_config_location(
    config_directory: Optional[Path] = None,
) -> Tuple[Path, Path]:
    """
    Try to find the configuration directory and file for astrality, based on
    filesystem or specific environment variables if they are present several
    places to put it. See README.md.
    """
    if not config_directory:
        if 'ASTRALITY_CONFIG_HOME' in os.environ:
            # The user has set a custom config directory for astrality
            config_directory = Path(os.environ['ASTRALITY_CONFIG_HOME'])
        else:
            # Follow the XDG directory standard
            config_directory = Path(
                os.getenv('XDG_CONFIG_HOME', '~/.config'),
                'astrality',
            )

    config_file = Path(config_directory, 'astrality.conf')

    if not config_file.is_file():
        logger.warning(
            'Configuration file not found in its expected path '
            + str(config_file) +
            '.'
        )
        config_directory = Path(__file__).parents[1]
        config_file = Path(config_directory, 'astrality.conf.example')
        logger.warning(f'Using example configuration instead: "{config_file}"')
    else:
        logging.info(f'Using configuration file "{config_file}"')

    return config_directory, config_file


def dict_from_config_file(
    config_file: Path,
    with_env: Optional[bool] = True,
) -> Dict[str, Dict[str, str]]:
    """
    Return a dictionary that reflects the contents of `config_file`.

    If with_env=True, an 'env' section is inserted into the dictionary
    containing all the environment variables. This makes it possible to use
    variable interpolation in order to expand environment variables like this:

    ${env:NAME_OF_ENV_VARIABLE}
    """

    if not config_file.is_file():
        raise RuntimeError(f'Could not load config file "{config_file}".')

    config_parser = ConfigParser(interpolation=ExtendedInterpolation())
    config_parser.read(config_file)

    if with_env:
        # Insert new 'env' section into the contents of of ConfigParser before
        # using __get__() on it. This enables variable interpolation of
        # environment variables.
        config_parser['env'] = {}
        for name, value in os.environ.items():
            try:
                config_parser['env'][name] = os.path.expandvars(value)
            except ValueError as e:
                if 'invalid interpolation syntax' in str(e):
                    logger.warning(f'''
                    Could not use environment variable {name}={value}.
                    It is too complex for expansion, using unexpanded value
                    instead...
                    ''')
                    try:
                        config_parser['env'][name] = value
                    except ValueError:
                        # Troubles with recursive env variables.
                        # Example: ${debian_chroot:+($debian_chroot)}
                        logger.warning('Unsuccessful, skipping env variable.')
                else:
                    raise

    # Convert ConfigParser into a dictionary, performing all variable
    # interpolations at the same time
    conf_dict: Dict[str, Dict[str, str]] = {}
    for section_name, section in config_parser.items():
        conf_dict[section_name] = {}
        for option in section.keys():
            try:
                # Here we must be very careful when `get`ing values, as several
                # things can go wrong. See the exception handling below.
                value = section[option]
                conf_dict[section_name][option] = value
            except (ValueError, InterpolationMissingOptionError) as e:
                if 'invalid interpolation syntax' in str(e) or \
                   'Bad value substitution' in str(e):
                    raw_value = config_parser.get(section_name, option, raw=True)
                    conf_dict[section_name][option] = raw_value

                    logger.warning(f'''
                    Error: In section [{section_name}]:
                    Could not interpolate {option}={raw_value}.
                    Using raw value instead.
                    ''')
                    continue
                else:
                    raise

    return conf_dict


def infer_runtime_variables_from_config(
    config_directory: Path,
    config_file: Path,
    config: Resolver,
) -> Resolver:
    """Return infered runtime variables based on config file."""

    # Insert infered paths from config_directory
    config_module_paths = {
        module: Path(config_directory, 'conky_themes', module)
        for module
        in config['conky']['modules'].split()
    }

    conky_module_templates = {
        module: Path(path, 'template.conf')
        for module, path
        in config_module_paths.items()
    }

    wallpaper_theme_directory = Path(
        config_directory,
        'wallpaper_themes',
        config['wallpaper']['theme'],
    )

    timer_class = TIMERS[config['timer']['type']]
    periods = timer_class.periods

    wallpaper_paths = {
        period: list(wallpaper_theme_directory.glob(period + '.*'))[0]
        for period
        in periods
    }

    temp_directory = Path(os.environ.get('TMPDIR', '/tmp'), 'astrality')
    if not temp_directory.is_dir():
        os.mkdir(temp_directory)

    conky_temp_files = create_conky_temp_files(temp_directory, conky_module_templates)

    return Resolver({
        '_runtime': {
            'config_directory': config_directory,
            'config_file': config_file,
            'conky_module_paths': config_module_paths,
            'conky_module_templates': conky_module_templates,
            'wallpaper_theme_directory': wallpaper_theme_directory,
            'wallpaper_paths': wallpaper_paths,
            'conky_temp_files': conky_temp_files,
            'timer_class': timer_class,
            'periods': periods,
            'temp_directory': temp_directory,
        }
    })


def user_configuration(config_directory: Optional[Path] = None) -> Resolver:
    """
    Create a configuration dictionary which should directly reflect the
    hierarchy of a typical `astrality.conf` file. Users should be able to insert
    elements from their configuration directly into conky module templates. The
    mapping should be:

    ${astrality:conky:main_font} -> config['conky']['main_font']

    Some additional configurations are automatically added to the root level of
    the dictionary such as:
    - config['config_directory']
    - config['config_file']
    - config['conky_module_paths']
    """
    config_directory, config_file = infer_config_location(config_directory)

    config = Resolver(dict_from_config_file(
        config_file,
        with_env=True,
    ))
    config.update(infer_runtime_variables_from_config(config_directory, config_file, config))

    # Import the colorscheme specified by the users wallpaper theme
    config.update(import_colors(config))



    return config
