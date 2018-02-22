"""Specifies everything related to application spanning configuration."""

import logging
import os
import re
from distutils.dir_util import copy_tree
from io import StringIO
from pathlib import Path
from typing import (
    Any,
    Dict,
    List,
    Match,
    MutableMapping,
    Optional,
    Tuple,
    Iterable,
)

from mypy_extensions import TypedDict

from astrality import compiler
from astrality.resolver import Resolver
from astrality.utils import run_shell

Context = Dict[str, Resolver]

logger = logging.getLogger('astrality')

from yaml import load, dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper  # type: ignore
    logger.info('Using LibYAML bindings for faster .yaml parsing.')
except ImportError:  # pragma: no cover
    from yaml import Loader, Dumper
    logger.warning(
        'LibYAML not installed.'
        'Using somewhat slower pure python implementation.',
    )


ApplicationConfig = Dict[str, Dict[str, Any]]

ASTRALITY_DEFAULT_GLOBAL_SETTINGS = {'settings/astrality': {
    'hot_reload_config': False,
    'recompile_modified_templates': False,
    'startup_delay': 0,
    'run_timeout': 0,
    'requires_timeout': 1,
}}


def resolve_config_directory() -> Path:
    """
    Return the absolute configuration directory path for the application.

    The directory path is resolved as follows:
        1) If $ASTRALITY_CONFIG_HOME is present, use it.
        2) If $XDG_CONFIG_HOME is present, use $XDG_CONFIG_HOME/astrality.
        3) Elsewise, use ~/config/astrality.
    """
    if 'ASTRALITY_CONFIG_HOME' in os.environ:
        # The user has set a custom config directory for astrality
        config_directory = Path(os.environ['ASTRALITY_CONFIG_HOME'])
    else:
        # Follow the XDG directory standard
        config_directory = Path(
            os.getenv('XDG_CONFIG_HOME', '~/.config'),
            'astrality',
        )
    return config_directory.expanduser().absolute()


def infer_config_location(
    config_directory: Optional[Path] = None,
) -> Tuple[Path, Path]:
    """
    Return path of Astrality configuration file based on config folder path.

    Try to find the configuration directory and file for astrality, based on
    filesystem or specific environment variables if they are present several
    places to put it. If the expected config file is not present, use an
    example configuration instead.
    """
    if not config_directory:
        config_directory = resolve_config_directory()
    config_file = Path(config_directory, 'astrality.yaml')

    if not config_file.is_file():
        logger.warning(
            'Configuration file not found in its expected path '
            + str(config_file) +
            '.'
        )
        config_directory = Path(__file__).parent.absolute() / 'config'
        config_file = config_directory / 'astrality.yaml'
        logger.warning(f'Using example configuration instead: "{config_file}"')
    else:
        logging.info(f'Using configuration file "{config_file}"')

    return config_directory, config_file


def dict_from_config_file(
    config_file: Path,
    with_env: bool = True,
) -> ApplicationConfig:
    """
    Return a dictionary that reflects the contents of `config_file`.

    Environment variables are interpolated like this:
        ${env:NAME_OF_ENV_VARIABLE} -> os.environ[NAME_OF_ENV_VARIABLE]

    If with_env=True, an 'env' section is inserted into the dictionary
    containing all the environment variables.
    """

    if not config_file.is_file():  # pragma: no cover
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
        conf_dict['context/env'] = expanded_env_dict

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

    # Insert default global settings that are not specified
    user_settings = config.get('settings/astrality', {})
    config['settings/astrality'] = ASTRALITY_DEFAULT_GLOBAL_SETTINGS['settings/astrality'].copy()
    config['settings/astrality'].update(user_settings)

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
    working_directory = conf_file.parent

    conf_text = ''
    with open(conf_file, 'r') as file:
        for line in file:
            conf_text += insert_environment_values(
                insert_command_substitutions(
                    content=line,
                    shell_command_working_directory=working_directory
                ),
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
        env_variable = match.groups()[0]
        try:
            return env_dict[env_variable]
        except KeyError:
            logging.error(
                f'Could not insert environment variable {env_variable}. '
                'It is not defined. Leaving it as is in the configuration.'
            )
            return '${' + env_variable + '}'

    return env_variable_pattern.sub(
        expand_environment_variable,
        content,
    )


def insert_command_substitutions(
    content: str,
    shell_command_working_directory: Path,
) -> str:
    """Replace all occurences in string: $(command) -> command stdout."""
    command_substitution_pattern = re.compile(r'\$\((.*)\)')

    def command_substitution(match: Match[str]) -> str:
        command = match.groups()[0]
        result = run_shell(
            command=command,
            working_directory=shell_command_working_directory,
        )
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
    context: Context,
    from_config_file: Path,
    section: Optional[str],
    from_section: Optional[str],
) -> Context:
    """
    Import section(s) from config file into config dictionary.

    If `section` and `from_section` are given:
    The method overwrites `config[section]` with the values from [from_section]
    defined in `from_config_file`.

    Else:
    All sections are imported from `from_config_file`.
    """
    logger.info(
        f'Importing context section {section} from {str(from_config_file)}',
    )

    contexts = compiler.context(dict_from_config_file(
        from_config_file,
        with_env=False,
    ))

    if section and from_section:
        # A specific source and target section has been specified
        context[section] = contexts[from_section]
    else:
        # All sections should be merged into the context
        context.update(contexts)

    return context


def create_config_directory(path: Optional[Path]=None, empty=False) -> Path:
    """Create application configuration directory and return its path."""
    if not path:
        path = resolve_config_directory()

    if not path.exists():
        if empty:
            logger.warning(f'Creating empty directory at "{str(path)}".')
            path.mkdir(parents=True)
        else:
            logger.warning(f'Copying over example config directory to "{str(path)}".')
            example_config_dir = Path(__file__).parent / 'config'
            copy_tree(
                src=str(example_config_dir),
                dst=str(path),
            )
    else:
        logger.warning(f'Path "{str(path)}" already exists! Delete it first.')

    return path

def expand_path(path: Path, config_directory: Path) -> Path:
    """
    Return an absolute path from a (possibly) relative path.

    Relative paths are relative to $ASTRALITY_CONFIG_HOME, and ~ is
    expanded to the home directory of $USER.
    """

    path = Path.expanduser(path)

    if not path.is_absolute():
        path = Path(
            config_directory,
            path,
        )

    return path


class ExternalModuleDictRequired(TypedDict):
    name: str


class ExternalModuleDict(ExternalModuleDictRequired, total=False):
    """Dictionary defining an externally defined module."""
    safe: bool


ModuleConfig = Dict[str, Any]


class ExternalModuleSource:
    """
    Module defined outside of `$ASTRALITY_CONFIG_HOME/astrality.yaml.

    The module is represented by a directory, and possibly in the future by
    an url.
    """
    # The name of the module
    name: str

    # The directory containing all the files which represent the module,
    # by default $ASTRALITY_CONFIG_HOME/modules/{name}
    directory: Path

    # Path to the YAML configuration of the module:
    # Default: {directory}/modules.yaml
    config_file: Path

    # If the module is considered safe (i.e. allows shell execution)
    safe: bool

    def __init__(
        self,
        config: ExternalModuleDict,
        config_directory: Path,
        modules_directory_path: Path,
    ) -> None:
        """
        Initialize an ExternalModule object.
        """
        self.name = config['name']
        self.directory = expand_path(
            path=modules_directory_path / Path(self.name),
            config_directory=config_directory,
        )
        self.config_file = self.directory / 'modules.yaml'
        self.safe = config.get('safe', False)

    def module_config_dict(self) -> ModuleConfig:
        """Return the contents of `modules.yaml` as a dictionary."""
        modules_dict = dict_from_config_file(
            config_file=self.config_file,
            with_env=False,
        )

        # We rename each module to module/module_name[path_to_module_directory]
        # in order to prevent naming conflicts when using modules provided
        # from a third party with the same name as another managed module.
        # This way you can use a module named "conky" from two third parties,
        # in addition to providing your own.
        for section in tuple(modules_dict.keys()):
            if len(section) > 7 and section[:7].lower() == 'module/':
                non_conflicting_module_name = str(section) + f'[{self.directory}]'
                module_section = modules_dict.pop(section)
                modules_dict[non_conflicting_module_name] = module_section

        return modules_dict

    def __repr__(self):
        """Human-readable representation of a ExternalModuleSource object."""
        return f'ExternalModuleSource(name={self.name}, directory={self.directory}, safe={self.safe})'

    def __eq__(self, other) -> bool:
        """
        Return true if two ExternalModuleSource objects represents the same Module.

        Entirily determined by the source directory of the module.
        """
        try:
            return self.directory == other.directory
        except:
            return False


class GlobalModulesConfigDict(TypedDict, total=False):
    """Dictionary defining configuration options for Modules."""
    modules_directory_path: str
    enabled: List[ExternalModuleDict]


class GlobalModulesConfig:
    """User modules configuration."""

    # The path to the modules directory, by default:
    # $ASTRALITY_CONFIG_HOME/modules
    modules_directory_path: Path

    # All extenally managed modules
    external_module_sources: Iterable[ExternalModuleSource]

    # The absolute path to all module config files of name `modules.yaml`
    external_module_config_files: Iterable[Path]

    def __init__(
        self,
        config: GlobalModulesConfigDict,
        config_directory: Path,
    ) -> None:
        """Initialize a GlobalModulesConfig object from a dictionary."""

        # Determine the directory which contains external modules
        if 'modules_directory_path' in config:
            # Custom modules folder
            modules_path = expand_path(
                path=Path(config['modules_directory_path']),
                config_directory=config_directory,
            )
            self.modules_directory_path = modules_path
        else:
            # Default modules folder: $ASTRALITY_CONFIG_HOME/modules
            self.modules_directory_path = config_directory / 'modules'

        # Initialize all the external module sources
        self._external_module_sources: Dict[Path, ExternalModuleSource] = {}
        for external_module_dict in config.get('enabled', []):
            external_module_source = ExternalModuleSource(
                config=external_module_dict,
                modules_directory_path=self.modules_directory_path,
                config_directory=config_directory,
            )
            self._external_module_sources[external_module_source.directory] = \
                external_module_source

    @property
    def external_module_sources(self) -> Iterable[ExternalModuleSource]:
        """Return an iterator yielding all ExternalModuleSource objects."""
        for external_module_source in self._external_module_sources.values():
            yield external_module_source

    @property
    def external_module_config_files(self) -> Iterable[Path]:
        """Return an iterator yielding all absolute paths to module config files."""
        for external_module_source in self._external_module_sources.values():
            yield external_module_source.config_file

    def module_configs_dict(self) -> ModuleConfig:
        """Return a merged dictionary of all the externally managed module configs."""
        module_config_dict = {}
        for external_module_source in self._external_module_sources.values():
            module_config_dict.update(external_module_source.module_config_dict())

        return module_config_dict
