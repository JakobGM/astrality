"""Specifies everything related to application spanning configuration."""

import copy
import logging
import os
import re
from abc import ABC, abstractmethod
from distutils.dir_util import copy_tree
from pathlib import Path
from typing import (
    Any,
    Dict,
    ClassVar,
    List,
    Optional,
    Pattern,
    Set,
    Tuple,
    TYPE_CHECKING,
    Type,
    Iterable,
    Union,
)

from mypy_extensions import TypedDict

from astrality.exceptions import (
    MisconfiguredConfigurationFile,
    NonExistentEnabledModule,
)
from astrality.github import clone_repo, clone_or_pull_repo
from astrality.context import Context
from astrality import utils
from astrality.persistence import CreatedFiles

if TYPE_CHECKING:
    from astrality.module import ModuleConfigDict  # noqa

logger = logging.getLogger(__name__)


class EnablingStatementRequired(TypedDict):
    """Required items of astrality.yml::modules:enabled_modules."""

    name: str


class EnablingStatement(EnablingStatementRequired, total=False):
    """Optional items of astrality.yml::modules:enabled_modules."""

    trusted: bool
    autoupdate: bool


class GlobalModulesConfigDict(TypedDict, total=False):
    """Optional items in astrality.yml::modules."""

    requires_timeout: Union[int, float]
    run_timeout: Union[int, float]
    reprocess_modified_files: bool
    modules_directory: str
    enabled_modules: List[EnablingStatement]


class GlobalAstralityConfigDict(TypedDict, total=False):
    """Optional items in astrality.yml::astrality."""

    hot_reload_config: bool
    startup_delay: Union[int, float]


class AstralityYAMLConfigDict(TypedDict, total=False):
    """Optional items in astrality.yml."""

    astrality: GlobalAstralityConfigDict
    modules: GlobalModulesConfigDict


ASTRALITY_DEFAULT_GLOBAL_SETTINGS: AstralityYAMLConfigDict = {
    'astrality': {
        'hot_reload_config': False,
        'startup_delay': 0,
    },
    'modules': {
        'requires_timeout': 1,
        'run_timeout': 0,
        'reprocess_modified_files': False,
        'modules_directory': 'modules',
        'enabled_modules': [
            {'name': '*'},
            {'name': '*::*'},
        ],
    },
}


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
            'Configuration file not found in its expected path ' +
            str(config_file) +
            '.',
        )
        config_directory = Path(__file__).parent.absolute() / 'config'
        config_file = config_directory / 'astrality.yml'
        logger.warning(f'Using example configuration instead: "{config_file}"')
    else:
        logging.info(f'Using configuration file "{config_file}"')

    return config_directory, config_file


def user_configuration(
    config_directory: Optional[Path] = None,
) -> Tuple[
    AstralityYAMLConfigDict,
    Dict[str, 'ModuleConfigDict'],
    Context,
    Path,
]:
    """
    Return instantiation parameters for ModuleManager.

    :return: Tuple containing: astrality.yml dictionary, global modules
        dictionary, global context dictionary, and path to config directory.
    """
    config_directory, config_file = infer_config_location(config_directory)

    # First get global context, which we can use when compiling other files
    context_file = config_directory / 'context.yml'
    if context_file.exists():
        global_context = Context(utils.compile_yaml(
            path=context_file,
            context=Context(),
        ))
    else:
        global_context = Context()

    # Global configuration options
    config: AstralityYAMLConfigDict = utils.compile_yaml(  # type: ignore
        path=config_file,
        context=global_context,
    )

    # Insert default global settings that are not specified
    for section_name in ('astrality', 'modules'):
        section_content = config.get(section_name, {})
        config[section_name] = ASTRALITY_DEFAULT_GLOBAL_SETTINGS[section_name].copy()  # type: ignore # noqa
        config[section_name].update(section_content)  # type: ignore

    # Globally defined modules
    modules_file = config_directory / 'modules.yml'
    if modules_file.exists():
        modules = utils.compile_yaml(
            path=modules_file,
            context=global_context,
        )
    else:
        modules = {}

    return config, modules, global_context, config_directory


def create_config_directory(path: Optional[Path] = None, empty=False) -> Path:
    """Create application configuration directory and return its path."""
    if not path:
        path = resolve_config_directory()

    if not path.exists():
        if empty:
            logger.warning(f'Creating empty directory at "{str(path)}".')
            path.mkdir(parents=True)
        else:
            logger.warning(
                f'Copying over example config directory to "{str(path)}".',
            )
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
    # Expand environment variables present in path
    path = Path(os.path.expandvars(path))  # type: ignore

    # Expand any tilde expressions for user home directory
    path = path.expanduser()

    # Use config directory as anchor for relative paths
    if not path.is_absolute():
        path = Path(os.path.expandvars(config_directory)) / path  # type: ignore

    # Return path where symlinks such as '..' are resolved
    return path.resolve()


def expand_globbed_path(path: Path, config_directory: Path) -> Set[Path]:
    """
    Expand globs, i.e. * and **, of path object.

    This function is actually not used at the moment, but I have left it here
    in case we would want to support globbed paths in the future.

    :param path: Path to be expanded.
    :param config_directory: Anchor for relative paths.
    :return: Set of file paths resulting from glob expansion.
    """
    # Make relative paths absolute with config_directory as anchor
    path = expand_path(path=path, config_directory=config_directory)

    # Remove root directory from path
    relative_to_root = Path(*path.parts[1:])

    # Expand all globs in the entirety of `path`, recursing if ** is present
    expanded_paths = Path('/').glob(
        pattern=str(relative_to_root),
    )

    # Cast generator to set, and remove directories
    return set(path for path in expanded_paths if path.is_file())


class ModuleSource(ABC):
    """Superclass for the source of an enabled module."""

    # Directory containing "modules.yml" and "context.yml"
    directory: Path

    # Path to "modules.yml"
    modules_file: Path

    # Path to "context.yml"
    context_file: Path

    # Name syntax defining how to enable this module source type
    name_syntax: ClassVar[Pattern]

    # What to prepend to module names in order to avoid name collisions
    prepend: str

    # String specifying which modules that are enabled in module source
    enabled_module: str

    # Cached property containing module configurations
    _modules: Dict[str, 'ModuleConfigDict']

    # Cached property containing module context
    _context: Context

    # Options defined in astrality.yml
    _config: Dict[str, 'ModuleConfigDict']

    @abstractmethod
    def __init__(
        self,
        enabling_statement: EnablingStatement,
        modules_directory: Path,
    ) -> None:
        """Initialize a module source from an enabling statement."""
        raise NotImplementedError

    def modules(self, context: Context) -> Dict[Any, Any]:
        """
        Return modules defined in modules source.

        :param context: Context used when compiling "modules.yml".
        :return: Modules dictionary, with module name keys prepended with
            '/module', and module configuration values.
        """
        if not self.modules_file.exists():
            self._modules = {}

        if hasattr(self, '_modules'):
            return self._modules

        self._modules = filter_config_file(
            config_file=self.modules_file,
            context=context,
            enabled_module_name=self.enabled_module,
            prepend=self.prepend,
        )
        return self._modules

    def context(self, context: Context = Context()) -> Context:
        """
        Return context defined in module source.

        :param context: Context used when compiling "context.yml".
        :return: Context dictionary.
        """
        if not self.context_file.exists():
            return Context()

        if hasattr(self, '_context'):
            return self._context

        self._context = Context(utils.compile_yaml(
            path=self.context_file,
            context=context,
        ))
        return self._context

    def config(
        self,
        context: Context = Context(),
    ) -> Dict[str, 'ModuleConfigDict']:
        """
        Return all configuration options defined in module source.

        This includes modules (prepended with 'module/') and context (prepended
        with 'context/'.

        :param context: Context used when compiling "modules.yml" and
            "context.yml".
        :return: Module and context dictionary.
        """
        if hasattr(self, '_config'):
            return self._config

        self._config = self.modules(context=context)
        return self._config

    def __contains__(self, module_name: str) -> bool:
        """Return True if this source contains enabled module_name."""
        return module_name in self._modules

    @classmethod
    def represented_by(cls, module_name: str) -> bool:
        """Return True if name represents module source type."""
        return bool(cls.name_syntax.match(module_name))

    @classmethod
    def type(cls, of: str) -> 'ModuleSource':
        """Return the subclass which is responsible for the module name."""
        for source_type in cls.__subclasses__():
            if source_type.represented_by(module_name=of):
                return source_type

        raise MisconfiguredConfigurationFile(  # pragma: no cover
            f'Tried to enable invalid module name syntax "{of}".',
        )


class GlobalModuleSource(ModuleSource):
    """Module defined in `$ASTRALITY_CONFIG_HOME/modules.yml`."""

    name_syntax = re.compile(r'^(\w+|\*)$')
    prepend = ''

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
        self.modules_file = modules_directory / 'modules.yml'
        self.context_file = modules_directory / 'context.yml'

    def __contains__(self, module_name: str) -> bool:
        """Return True if the module name is enabled."""
        if self.enabled_module == '*' and self.represented_by(module_name):
            return True
        else:
            return module_name == self.enabled_module

    def __repr__(self) -> str:
        """Return the string representation of the global module source."""
        return f"GlobalModuleSource('{self.enabled_module}')"


class GithubModuleSource(ModuleSource):
    """Module defined in a GitHub repository."""

    name_syntax = re.compile(r'^github::.+/.+(::(\w+|\*))?$')

    def __init__(
        self,
        enabling_statement: EnablingStatement,
        modules_directory: Path,
    ) -> None:
        """
        Initialize enabled module defined in Github repository.

        A GitHub module is enabled with the name syntax:
        github::<github_user>/<github_repo>[::<enabled_module>]

        If <enabled_module> is skipped, all modules are enabled, i.e.
        github::<github_user>/<github_repo>::*
        """
        assert self.represented_by(
            module_name=enabling_statement['name'],
        )
        assert modules_directory.is_absolute()

        specified_module = enabling_statement['name']
        self.autoupdate = enabling_statement.get('autoupdate', False)

        github_path, *enabled_modules = specified_module[8:].split('::')
        if len(enabled_modules) > 0:
            self.enabled_module = enabled_modules[0]
        else:
            self.enabled_module = '*'

        self.github_user, self.github_repo = github_path.split('/')
        self.prepend = f'github::{self.github_user}/{self.github_repo}::'

        self.directory = modules_directory \
            / self.github_user \
            / self.github_repo
        self.modules_file = self.directory / 'modules.yml'
        self.context_file = self.directory / 'context.yml'

        if not self.directory.is_dir():
            clone_repo(
                user=self.github_user,
                repository=self.github_repo,
                modules_directory=modules_directory,
            )
        elif self.autoupdate:
            clone_or_pull_repo(
                user=self.github_user,
                repository=self.github_repo,
                modules_directory=modules_directory,
            )

    def __eq__(self, other) -> bool:
        """
        Return True if being compared to identical github module.

        Return True if two GithubModuleSource objects represent the same
        directory with identical modules enabled.
        """
        try:
            return self.directory == other.directory \
                and self._config == other._config
        except AttributeError:
            return False

    def __repr__(self) -> str:
        """Return string representation of the github module source."""
        return f"GithubModuleSource('{self.github_user}/{self.github_repo}')" \
            f' = {tuple(self._config.keys())}'


class DirectoryModuleSource(ModuleSource):
    """
    Module(s) defined in a directory.

    Specifically: `$ASTRALITY_CONFIG_HOME/{modules_directory}/config.yml
    """

    name_syntax = re.compile(r'^(?!github::).+::(\w+|\*)$')

    def __init__(
        self,
        enabling_statement: EnablingStatement,
        modules_directory: Path,
    ) -> None:
        """Initialize an DirectoryModuleSource object."""
        assert self.represented_by(
            module_name=enabling_statement['name'],
        )
        assert modules_directory.is_absolute()

        relative_directory_path, self.enabled_module = \
            enabling_statement['name'].split('::')
        self.relative_directory_path = Path(relative_directory_path)
        self.prepend = str(self.relative_directory_path) + '::'
        self.trusted = enabling_statement.get('trusted', True)

        self.directory = expand_path(
            path=self.relative_directory_path,
            config_directory=modules_directory,
        )
        self.modules_file = self.directory / 'modules.yml'
        self.context_file = self.directory / 'context.yml'

    def __repr__(self):
        """Human-readable representation of a DirectoryModuleSource object."""
        return ''.join((
            'DirectoryModuleSource(',
            f'name={self.relative_directory_path}::',
            f'{self.enabled_module_name}, ',
            f'directory={self.directory}, ',
            f'trusted={self.trusted})',
        ))

    def __eq__(self, other) -> bool:
        """
        Return true if compared to identical module defined in a directory.

        Entirily determined by the source directory of the module.
        """
        try:
            return self.directory == other.directory
        except AttributeError:  # pragma: no cover
            return False


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
            try:
                source_type = ModuleSource.type(of=enabling_statement['name'])
            except MisconfiguredConfigurationFile:
                logger.error(
                    f'Invalid module name syntax {str(enabling_statement)} '
                    'in enabled_modules configuration.',
                )
                continue

            if source_type == GlobalModuleSource:
                source_directory = config_directory
            else:
                source_directory = modules_directory

            self.source_types[source_type].append(source_type(
                enabling_statement=enabling_statement,
                modules_directory=source_directory,
            ))

    def process_enabling_statements(
        self,
        enabling_statements: List[EnablingStatement],
        modules_directory: Path,
    ):
        """Return enabling statements where wildcards have been replaced."""
        self.all_global_modules_enabled = False
        self.all_directory_modules_enabled = False

        new_enabling_statements: List[EnablingStatement] = []
        for enabling_statement in enabling_statements:
            if enabling_statement['name'] == '*':
                self.all_global_modules_enabled = True
                new_enabling_statements.append(enabling_statement)

            elif enabling_statement['name'] == '*::*':
                self.all_directory_modules_enabled = True

                for module_directory in self.module_directories(
                    within=modules_directory,
                ):
                    directory_module = module_directory + '::*'
                    new_enabling_statement = copy.deepcopy(enabling_statement)
                    new_enabling_statement['name'] = directory_module
                    new_enabling_statements.append(new_enabling_statement)

            else:
                new_enabling_statements.append(enabling_statement)

        return new_enabling_statements

    @staticmethod
    def module_directories(within: Path) -> Tuple[str, ...]:
        """Return all subdirectories which contain module definitions."""
        try:
            return tuple(
                path.name
                for path
                in within.glob('**/*')
                if (path / 'modules.yml').is_file() or
                (path / 'context.yml').is_file()
            )
        except FileNotFoundError:
            logger.error(
                f'Tried to search for module directories in "{within}", '
                'but directory does not exist!.',
            )
            return ()

    def compile_config_files(
        self,
        context: Context,
    ):
        """Compile all config templates with context."""
        for source in (
            *self.source_types[DirectoryModuleSource],
            *self.source_types[GithubModuleSource],
        ):
            source.config(context=context)

    def __contains__(self, module_name: str) -> bool:
        """Return True if the given module name is supposed to be enabled."""
        source_type = ModuleSource.type(of=module_name)
        for module_source in self.source_types[source_type]:
            if module_name in module_source:
                return True

        return False

    def __repr__(self) -> str:
        """Return string representation of all enabled modules."""
        return ', '.join(
            source.__repr__()
            for source
            in self.source_types.values()
        )


class GlobalModulesConfig:
    """
    User modules configuration.

    The plan is to make this the input argument for ModuleManager.__init__(),
    extracting all logic related to getting module configurations (only enebled
    ones) from the object.
    """

    def __init__(
        self,
        config: GlobalModulesConfigDict,
        config_directory: Path,
    ) -> None:
        """Initialize a GlobalModulesConfig object from a dictionary."""
        self.reprocess_modified_files = config.get(
            'reprocess_modified_files',
            False,
        )
        self.requires_timeout = config.get(
            'requires_timeout',
            1,
        )
        self.run_timeout = config.get(
            'run_timeout',
            0,
        )
        self.created_files = CreatedFiles()

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
                    {'name': '*::*', 'trusted': True},
                ],
            ),
            config_directory=self.config_directory,
            modules_directory=self.modules_directory,
        )

    @property
    def external_module_sources(
        self,
    ) -> Iterable[ModuleSource]:
        """Return an iterator yielding all external module configs."""
        for source in (
            *self.enabled_modules.source_types[DirectoryModuleSource],
            *self.enabled_modules.source_types[GithubModuleSource],
        ):
            yield source

    def compile_config_files(
        self,
        context: Context,
    ):
        """Compile all config templates with context."""
        self.enabled_modules.compile_config_files(context)


def filter_config_file(
    config_file: Path,
    context: Context,
    enabled_module_name: str,
    prepend: str,
) -> Dict[str, 'ModuleConfigDict']:
    """
    Return a filtered dictionary representing `config_file`.

    Only modules given by `enabled_module_name` are kept, and their names
    are prepended with `prepend`.
    """
    assert config_file.name == 'modules.yml'

    try:
        modules_dict = utils.compile_yaml(
            path=config_file,
            context=context,
        )
    except FileNotFoundError:
        logger.warning(
            f'Non-existent module configuration file "{config_file}" '
            'Skipping enabled module '
            f'"{prepend}{enabled_module_name}"',
        )
        return {}

    if not modules_dict:  # pragma: no cover
        logger.warning(
            f'Empty modules configuration "{config_file}".',
        )
        return {}
    elif not isinstance(modules_dict, dict):  # pragma: no cover
        logger.critical(
            f'Configuration file "{config_file}" not formated as '
            'a dictionary at root indentation.',
        )
        raise MisconfiguredConfigurationFile

    modules = tuple(modules_dict.keys())
    if enabled_module_name != '*' \
            and enabled_module_name not in modules:
        raise NonExistentEnabledModule

    # We rename each module to module/{self.name}.module_name
    # in order to prevent naming conflicts when using modules provided
    # from a third party with the same name as another managed module.
    # This way you can use a module named "conky" from two third parties,
    # in addition to providing your own.
    for module_name in modules:
        if not enabled_module_name == '*' \
           and enabled_module_name != module_name:
            # The module is not enabled, remove the module
            modules_dict.pop(module_name)
            continue

        # Replace the module name with folder_name.module_name
        non_conflicting_module_name = prepend + module_name
        module_section = modules_dict.pop(module_name)
        modules_dict[non_conflicting_module_name] = module_section

    return modules_dict
