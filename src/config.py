"""Specifies everything related to application spanning configuration."""

import logging
import os
from pathlib import Path
import re
from io import StringIO
from typing import Any, Dict, Match, MutableMapping, Optional, Tuple

from utils import run_shell

logger = logging.getLogger('astrality')

from yaml import load, dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper  # type: ignore
    logger.info('Using LibYAML bindings for faster .yaml parsing.')
except ImportError:
    from yaml import Loader, Dumper
    logger.warning(
        'LibYAML not installed.'
        'Using somewhat slower pure python implementation.',
    )


ApplicationConfig = Dict[str, Dict[str, Any]]


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

    config_file = Path(config_directory, 'astrality.yaml')

    if not config_file.is_file():
        logger.warning(
            'Configuration file not found in its expected path '
            + str(config_file) +
            '.'
        )
        config_directory = Path(__file__).parents[1]
        config_file = Path(config_directory, 'astrality.yaml.example')
        logger.warning(f'Using example configuration instead: "{config_file}"')
    else:
        logging.info(f'Using configuration file "{config_file}"')

    return config_directory, config_file


def dict_from_config_file(
    config_file: Path,
    with_env: Optional[bool] = True,
) -> ApplicationConfig:
    """
    Return a dictionary that reflects the contents of `config_file`.

    Environment variables are interpolated like this:
        ${env:NAME_OF_ENV_VARIABLE} -> os.environ[NAME_OF_ENV_VARIABLE]

    If with_env=True, an 'env' section is inserted into the dictionary
    containing all the environment variables.
    """

    if not config_file.is_file():
        error_msg = f'Could not load config file "{config_file}".'
        logger.critical(error_msg)
        raise RuntimeError(error_msg)

    expanded_env_dict = generate_expanded_env_dict()
    config_string = preprocess_configuration_file(
        config_file,
        expanded_env_dict,
    )
    conf_dict = load(StringIO(config_string))

    if with_env:
        conf_dict['env'] = expanded_env_dict

    return conf_dict


def infer_runtime_variables_from_config(
    config_directory: Path,
    config_file: Path,
    config: ApplicationConfig,
) -> Dict[str, Dict[str, Path]]:
    """Return infered runtime variables based on config file."""

    temp_directory = Path(os.environ.get('TMPDIR', '/tmp')) / 'astrality'
    if not temp_directory.is_dir():
        os.mkdir(temp_directory)

    return {
        '_runtime': {
            'config_directory': config_directory,
            'config_file': config_file,
            'temp_directory': temp_directory,
        }
    }


def user_configuration(config_directory: Optional[Path] = None) -> ApplicationConfig:
    """
    Return Resolver object containing the users configuration.

    Create a configuration dictionary which should directly reflect the
    hierarchy of a typical `astrality.yaml` file. Users should be able to insert
    elements from their configuration directly into conky module templates. The
    mapping should be:

    ${astrality:fonts:1} -> config['fonts']['1']

    In addition, the section config['_runtime'] is inserted, which contains
    several items specifying runtime specific values. Example keys are:
    - config_directory
    - config_file
    - temp_directory
    """
    config_directory, config_file = infer_config_location(config_directory)

    config = dict_from_config_file(
        config_file,
        with_env=True,
    )
    config.update(infer_runtime_variables_from_config(
        config_directory,
        config_file,
        config,
    ))

    return config

def preprocess_configuration_file(
    conf_file: Path,
    env_dict: MutableMapping[str, str] = os.environ,
) -> str:
    """
    Interpolate environment variables and command substitutions in file.

    Interpolation syntax:
        ${name} -> os.environ[name].
        $(command) -> stdout from shell execution.
    """

    conf_text = ''
    with open(conf_file, 'r') as file:
        for line in file:
            conf_text += insert_environment_values(
                insert_command_substitutions(line),
                env_dict,
            )

    return conf_text

def insert_environment_values(
    content: str,
    env_dict: MutableMapping[str, str] = os.environ,
) -> str:
    """Replace all occurences in string: ${name} -> env_dict[name]."""

    env_dict = generate_expanded_env_dict()
    env_variable_pattern = re.compile(r'\$\{(\w+)\}')

    def expand_environment_variable(match: Match[str]) -> str:
        return env_dict[match.groups()[0]]

    return env_variable_pattern.sub(
        expand_environment_variable,
        content,
    )


def insert_command_substitutions(content: str) -> str:
    """Replace all occurences in string: $(command) -> command stdout."""

    command_substitution_pattern = re.compile(r'\$\((.*)\)')

    def command_substitution(match: Match[str]) -> str:
        command = match.groups()[0]
        result = run_shell(command=command)
        if result == '':
            logger.error(
                f'Command substitution $({command}) returned empty stdout.'
            )
        return result

    return command_substitution_pattern.sub(
        command_substitution,
        content,
    )


def generate_expanded_env_dict() -> Dict[str, str]:
    """Return os.environ dict with all env variables expanded."""

    env_dict = {}
    for name, value in os.environ.items():
        try:
            env_dict[name] = os.path.expandvars(value)
        except ValueError as e:
            if 'invalid interpolation syntax' in str(e):
                logger.warning(f'''
                Could not use environment variable {name}={value}.
                It is too complex for expansion, using unexpanded value
                instead...
                ''')
                env_dict[name] = value
            else:
                raise

    return env_dict


def insert_into(
    config: Any,
    section: str,
    from_config_file: Path,
    from_section: str,
) -> Any:
    """
    Import section from config file into config dictionary.

    The method overwrites `config[section]` with the values from [from_section]
    defined in `from_config_file`.
    """
    conf_resolver = dict_from_config_file(from_config_file, with_env=False)
    config[section] = conf_resolver[from_section]

    return config
