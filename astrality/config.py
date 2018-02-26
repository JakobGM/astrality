"""Specifies everything related to application spanning configuration."""

import copy
import logging
import os
import re
from abc import ABC, abstractclassmethod, abstractmethod
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
    Pattern,
    Tuple,
    Type,
    Iterable,
)
import re

from mypy_extensions import TypedDict

from astrality import compiler
from astrality.exceptions import (
    MisconfiguredConfigurationFile,
    NonExistentEnabledModule,
)
from astrality.resolver import Resolver
from astrality.utils import run_shell

Context = Dict[str, Resolver]

logger = logging.getLogger('astrality')

from yaml import load, dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper  # type: ignore
    logger.info('Using LibYAML bindings for faster .yml parsing.')
except ImportError:  # pragma: no cover
    from yaml import Loader, Dumper
    logger.warning(
        'LibYAML not installed.'
        'Using somewhat slower pure python implementation.',
    )


ApplicationConfig = Dict[str, Dict[str, Any]]

ASTRALITY_DEFAULT_GLOBAL_SETTINGS = {'config/astrality': {
    'hot_reload_config': False,
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
    config_file = Path(config_directory, 'astrality.yml')

    if not config_file.is_file():
        logger.warning(
            'Configuration file not found in its expected path '
            + str(config_file) +
            '.'
        )
        config_directory = Path(__file__).parent.absolute() / 'config'
        config_file = config_directory / 'astrality.yml'
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
        raise FileNotFoundError(error_msg)

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
    hierarchy of a typical `astrality.yml` file. Users should be able to insert
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
    user_settings = config.get('config/astrality', {})
    config['config/astrality'] = ASTRALITY_DEFAULT_GLOBAL_SETTINGS['config/astrality'].copy()
    config['config/astrality'].update(user_settings)

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
    else:  # pragma: no cover
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


class EnablingStatementRequired(TypedDict):
    name: str


class EnablingStatement(EnablingStatementRequired, total=False):
    """Dictionary defining an externally defined module."""
    trusted: bool


ModuleConfig = Dict[str, Any]


class ModuleSource(ABC):

    @abstractmethod
    def __init__(
        self,
        enabling_statement: EnablingStatement,
        modules_directory: Path,
    ) -> None:
        """Initialize a module source from an enabling statement."""
        raise NotImplementedError

    @property
    @abstractmethod
    def name_syntax(self) -> Pattern:
        """Regular expression defining how to name this type of module source."""
        raise NotImplementedError

    @classmethod
    def represented_by(cls, module_name: str) -> bool:
        """Return True if name represents module source type."""
        return bool(cls.name_syntax.match(module_name))

    @classmethod
    def type(cls, of: str) -> Optional['ModuleSource']:
        """
        Return the source subclass which is responsible for the module name.
        """
        for source_type in cls.__subclasses__():
            if source_type.represented_by(module_name=of):
                return source_type

        raise MisconfiguredConfigurationFile(  # pragma: no cover
            f'Tried to enable invalid module name syntax "{of}".',
        )

    @abstractmethod
    def __contains__(self, module_name: str) -> bool:
        """Return True module source contains module with name `module_name`."""
        raise NotImplementedError


class GlobalModuleSource(ModuleSource):
    """Module defined in `astrality.yml`."""
    name_syntax = re.compile('^(\w+|\*)$')

    def __init__(
        self,
        enabling_statement: EnablingStatement,
        modules_directory: Path,
    ) -> None:
        """Initialize enabled module defined in `astrality.yml`."""
        self.enabled_module = enabling_statement['name']
        assert self.represented_by(module_name=self.enabled_module)

        assert modules_directory.is_absolute()
        self.directory = modules_directory

    def __contains__(self, module_name: str) -> bool:
        """Return True if the module name is enabled."""
        if self.enabled_module == '*' and self.represented_by(module_name):
            return True
        else:
            return module_name == self.enabled_module

    def __repr__(self) -> str:
        return f"GlobalModuleSource('{self.enabled_module}')"


class GithubModuleSource(ModuleSource):
    """Module defined in a GitHub repository."""
    name_syntax = re.compile('.+/.+')

    def __init__(
        self,
        enabling_statement: EnablingStatement,
        modules_directory: Path,
    ) -> None:
        """Initialize enabled module defined at https://github.com/{name}"""
        assert self.represented_by(
            module_name=enabling_statement['name'],
        )
        self.enabled_module = enabling_statement['name']
        self.github_user, self.github_repo = enabling_statement['name'].split('/')

    def __contains__(self, module_name: str) -> bool:
        """Return True if GitHub module repo is enabled."""
        if self.represented_by(module_name=module_name):
            return module_name == self.enabled_module
        else:
            return False

    def __repr__(self) -> str:
        return f"GithubModuleSource('{self.github_user}/{self.github_repo}')"


class DirectoryModuleSource(ModuleSource):
    """
    Module(s) defined in a directory.

    Specifically: `$ASTRALITY_CONFIG_HOME/{modules_directory}/config.yml
    """

    name_syntax = re.compile('^\w+\.(\w+|\*)$')

    def __init__(
        self,
        enabling_statement: EnablingStatement,
        modules_directory: Path,
    ) -> None:
        """
        Initialize an ExternalModule object.
        """
        assert self.represented_by(
            module_name=enabling_statement['name'],
        )
        self.category, self.enabled_module_name = enabling_statement['name'].split('.')

        assert modules_directory.is_absolute()
        self.directory = modules_directory / self.category

        self.config_file = self.directory / 'config.yml'
        self.trusted = enabling_statement.get('trusted', True)
        self.config = self._process_modules_config_dict(
            config_path=self.config_file,
        )

    def _process_modules_config_dict(self, config_path: Path) -> ModuleConfig:
        """
        Return the contents of `modules.yml` as a dictionary.

        Remove any defined modules which are not enabled by the
        enabling_statement.
        """
        try:
            modules_dict = dict_from_config_file(
                config_file=self.config_file,
                with_env=False,
            )
        except FileNotFoundError:
            logger.warning(
                f'Non-existent module configuration file "{self.config_file}"'
                'Skipping enabled module '
                f'"{self.category}.{self.enabled_module_name}"'
            )
            return {}
        if not modules_dict:  # pragma: no cover
            logger.warning(
                f'Empty modules configuration "{self.config_file}".',
            )
            return {}
        elif not isinstance(modules_dict, dict):  # pragma: no cover
            logger.critical(
                f'Configuration file "{self.config_file}" not formated as '
                'a dictionary at root indentation.'
            )
            raise MisconfiguredConfigurationFile

        sections = tuple(modules_dict.keys())
        if self.enabled_module_name != '*' \
                and 'module/' + self.enabled_module_name not in sections:
            raise NonExistentEnabledModule

        # We rename each module to module/{self.name}.module_name
        # in order to prevent naming conflicts when using modules provided
        # from a third party with the same name as another managed module.
        # This way you can use a module named "conky" from two third parties,
        # in addition to providing your own.
        for section in sections:
            if len(section) > 7 and section[:7].lower() == 'module/':
                # This section defines a module

                module_name = section[7:]
                if not self.enabled_module_name == '*' \
                   and self.enabled_module_name != module_name:
                    # The module is not enabled, remove the module
                    modules_dict.pop(section)
                    continue

                # Replace the module name with folder_name.module_name
                non_conflicting_module_name = \
                    'module/' + self.category + '.' + module_name
                module_section = modules_dict.pop(section)
                modules_dict[non_conflicting_module_name] = module_section

        return modules_dict

    def __repr__(self):
        """Human-readable representation of a DirectoryModuleSource object."""
        return f'DirectoryModuleSource(name={self.category}.{self.enabled_module_name}, directory={self.directory}, trusted={self.trusted})'

    def __eq__(self, other) -> bool:
        """
        Return true if two DirectoryModuleSource objects represents the same Module.

        Entirily determined by the source directory of the module.
        """
        try:
            return self.directory == other.directory
        except AttributeError:  # pragma: no cover
            return False

    def __contains__(self, module_name: str) -> bool:
        """Return True if source contains module named `module_name`."""
        return 'module/' + module_name in self.config


class EnabledModules:
    """
    Object which keeps track of all enabled modules.

    Also allows fetching of configurations defined externally.
    """

    def __init__(
        self,
        enabling_statements: List[EnablingStatement],
        config_directory: Path,
        modules_directory: Path,
    ) -> None:
        """Determine exactly which modules are enabled from user config."""
        enabling_statements = self.process_enabling_statements(
            enabling_statements=enabling_statements,
            modules_directory=modules_directory,
        )

        self.source_types: Dict[Type[ModuleSource], List[ModuleSource]] = {
            GlobalModuleSource: [],
            DirectoryModuleSource: [],
            GithubModuleSource: [],
        }

        for enabling_statement in enabling_statements:
            if GlobalModuleSource.represented_by(
                module_name=enabling_statement['name']
            ):
                self.source_types[GlobalModuleSource].append(
                    GlobalModuleSource(
                        enabling_statement=enabling_statement,
                        modules_directory=config_directory,
                    ),
                )
            elif DirectoryModuleSource.represented_by(
                module_name=enabling_statement['name'],
            ):
                self.source_types[DirectoryModuleSource].append(
                    DirectoryModuleSource(
                        enabling_statement=enabling_statement,
                        modules_directory=modules_directory,
                    ),
                )
            elif GithubModuleSource.represented_by(
                module_name=enabling_statement['name'],
            ):
                self.source_types[GithubModuleSource].append(
                    GithubModuleSource(
                        enabling_statement=enabling_statement,
                        modules_directory=modules_directory,
                    ),
                )
            else:
                logger.error(
                    f'Invalid module name syntax {str(enabling_statement)} '
                    'in enabled_modules configuration.'
                )

    def process_enabling_statements(
        self,
        enabling_statements: List[EnablingStatement],
        modules_directory: Path,
    ):
        """
        Return enabling statements where wildcards have been replaced.
        """
        self.all_global_modules_enabled = False
        self.all_directory_modules_enabled = False

        new_enabling_statements: List[EnablingStatement] = []
        for enabling_statement in enabling_statements:
            if enabling_statement['name'] == '*':
                self.all_global_modules_enabled = True
                new_enabling_statements.append(enabling_statement)

            elif enabling_statement['name'] == '*.*':
                self.all_directory_modules_enabled = True

                for module_directory in self.directory_names(within=modules_directory):
                    directory_module = module_directory + '.*'
                    new_enabling_statement = copy.deepcopy(enabling_statement)
                    new_enabling_statement['name'] = directory_module
                    new_enabling_statements.append(new_enabling_statement)

            else:
                new_enabling_statements.append(enabling_statement)

        return new_enabling_statements

    @staticmethod
    def directory_names(within: Path) -> Tuple[str, ...]:
        try:
            return tuple(
                path.name
                for path
                in within.iterdir()
                if path.is_dir()
            )
        except FileNotFoundError:
            logger.error(
                f'Tried to search for module directories in "{within}", '
                'but directory does not exist!.'
            )
            return ()

    def __contains__(self, module_name: str) -> bool:
        """Return True if the given module name is supposed to be enabled."""
        if module_name[:7].lower() == 'module/':
            module_name = module_name[7:]

        source_type = ModuleSource.type(of=module_name)
        for module_source in self.source_types[source_type]:
            if module_name in module_source:
                return True

        return False

    def __repr__(self) -> str:
        return ', '.join(
            source.__repr__()
            for source
            in self.source_types.values()
        )


class GlobalModulesConfigDict(TypedDict, total=False):
    """Dictionary defining configuration options for Modules."""
    recompile_modified_templates: bool
    modules_directory: str
    enabled_modules: List[EnablingStatement]


class GlobalModulesConfig:
    """User modules configuration."""

    def __init__(
        self,
        config: GlobalModulesConfigDict,
        config_directory: Path,
    ) -> None:
        """Initialize a GlobalModulesConfig object from a dictionary."""

        self.recompile_modified_templates = config.get(
            'recompile_modified_templates',
            False,
        )

        # Determine the directory which contains external modules
        assert config_directory.is_absolute()
        self.config_directory = config_directory
        if 'modules_directory' in config:
            # Custom modules folder
            modules_path = expand_path(
                path=Path(config['modules_directory']),
                config_directory=self.config_directory,
            )
            self.modules_directory = modules_path
        else:
            # Default modules folder: $ASTRALITY_CONFIG_HOME/modules
            self.modules_directory = config_directory / 'modules'

        # Enable all modules if nothing is specified
        self.enabled_modules = EnabledModules(
            enabling_statements=config.get(
                'enabled_modules',
                [
                    {'name': '*', 'trusted': True},
                    {'name': '*.*', 'trusted': True},
                ]
            ),
            config_directory=self.config_directory,
            modules_directory=self.modules_directory,
        )

    @property
    def external_module_sources(self) -> List[DirectoryModuleSource]:
        """Return an iterator yielding all DirectoryModuleSource objects."""
        return self.enabled_modules.source_types[DirectoryModuleSource]  # type: ignore

    @property
    def external_module_config_files(self) -> Iterable[Path]:
        """Return an iterator yielding all absolute paths to module config files."""
        for external_module_source in self.external_module_sources:
            yield external_module_source.config_file

    def module_configs_dict(self) -> ModuleConfig:
        """
        Return a merged dictionary of all directory module configs.

        TODO: Should at some point be responsible to return *all* module
        config dicts.
        """
        module_config_dict: ModuleConfig = {}
        for external_module_source in self.external_module_sources:
            module_config_dict.update(external_module_source.config)

        return module_config_dict
