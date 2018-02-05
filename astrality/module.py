"""Module implementing user configured custom functionality."""

from collections import namedtuple
from datetime import timedelta
import logging
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union

from astrality import compiler
from astrality.compiler import context
from astrality.config import ApplicationConfig, insert_into
from astrality.timer import Timer, timer_factory
from astrality.utils import run_shell

ModuleConfig = Dict[str, Any]
ContextSectionImport = namedtuple(
    'ContextSectionImport',
    ['into_section', 'from_section', 'from_config_file'],
)
logger = logging.getLogger('astrality')


class Module:
    """
    Class for determining module actions.

    A Module instance should only return actions to be performed, but never
    perform them. That is the responsibility of a ModuleManager instance.

    A module can define a set of commands to be run on astrality startup, and
    exit, in addition to every time a given type of period changes.

    Commands are run in the users shell, and can use the following placeholders:
    - {period}: The period specified by the timer instance.
    - {name_of_template}: The path to the compiled template specified in the
                          'target' option, or if not specified, a created
                          temporary file.
    """

    def __init__(
        self,
        module_config: ModuleConfig,
        config_directory: Path,
        temp_directory: Path,
    ) -> None:
        """
        Initialize Module object with a section from a config dictionary.

        Section name must be [module/*], where * is the module name.
        In addition, the enabled option must be set to "true", or not set at
        all.

        module_config example:
        {'module/name':
            'enabled': True,
            'timer': {'type': 'weekday'},
            'on_startup': ['echo weekday is {period}'],
        }
        """
        # Can only initialize one module at a time
        assert len(module_config) == 1

        section = next(iter(module_config.keys()))
        self.name: str = section.split('/')[1]

        self.module_config = module_config[section]
        self.config_directory = config_directory
        self.temp_directory = temp_directory

        # Use static timer if no timer is specified
        self.timer: Timer = timer_factory(
            self.module_config.get('timer', {'type': 'static'}),
        )

        # Find and prepare templates and compilation targets
        self._prepare_templates()

    def _prepare_templates(self) -> None:
        """Determine template sources and compilation targets."""
        # config['templates'] is a dictionary with keys naming each template,
        # and values containing another dictionary containing the mandatory
        # key `source`, and the optional key `target`.
        templates: Dict[str, Dict[str, str]] = self.module_config.get(
            'templates',
            {},
        )
        self.templates: Dict[str, Dict[str, Path]] = {}

        for name, template in templates.items():
            source = self.expand_path(Path(template['source']))

            if not source.is_file():
                logger.error(\
                    f'[module/{self.name}] Template "{name}": source "{source}"'
                    ' does not exist. Skipping compilation of this file.'
                )
                continue

            config_target = template.get('target')
            if config_target:
                target = self.expand_path(Path(config_target))
            else:
                target = self.create_temp_file()

            self.templates[name] = {'source': source, 'target': target}

    def create_temp_file(self) -> Path:
        """Create a temp file used as a compilation target, returning its path."""

        temp_file = NamedTemporaryFile(  # type: ignore
            prefix=self.name + '-',
            dir=self.temp_directory,
        )

        # NB: These temporary files need to be persisted during the entirity of
        # the scripts runtime, since the files are deleted when they go out of
        # scope.
        if not hasattr(self, 'temp_files'):
            self.temp_files = [temp_file]
        else:
            self.temp_files.append(temp_file)

        return Path(temp_file.name)

    def expand_path(self, path: Path) -> Path:
        """
        Return an absolute path from a (possibly) relative path.

        Relative paths are relative to $ASTRALITY_CONFIG_HOME, and ~ is
        expanded to the home directory of $USER.
        """

        path = Path.expanduser(path)

        if not path.is_absolute():
            path = Path(
                self.config_directory,
                path,
            )

        return path

    def startup_commands(self) -> Tuple[str, ...]:
        """Return commands to be run on Module instance startup."""
        startup_commands: List[str] = self.module_config.get(
            'run_on_startup',
            [],
        )

        if len(startup_commands) == 0:
            logger.debug(f'[module/{self.name}] No startup command specified.')
            return ()
        else:
            return tuple(
                self.interpolate_string(command)
                for command
                in startup_commands
            )

    def period_change_commands(self) -> Tuple[str, ...]:
        """Commands to be run when self.timer period changes."""
        period_change_commands: List[str] = self.module_config.get(
            'run_on_period_change',
            [],
        )

        if len(period_change_commands) == 0:
            logger.debug(f'[module/{self.name}] No period change command specified.')
            return ()
        else:
            return tuple(
                self.interpolate_string(command)
                for command
                in period_change_commands
            )

    def exit_commands(self) -> Tuple[str, ...]:
        """Commands to be run on Module instance shutdown."""
        exit_commands: List[str] = self.module_config.get(
            'run_on_exit',
            [],
        )

        if len(exit_commands) == 0:
            logger.debug(f'[module/{self.name}] No exit command specified.')
            return ()
        else:
            return tuple(
                self.interpolate_string(command)
                for command
                in exit_commands
            )

    def context_section_imports(self) -> Tuple[ContextSectionImport, ...]:
        """Return what to import into the global application_context."""
        context_section_imports = []
        import_config = self.module_config.get(
            'import_context_sections_on_period_change',
            [],
        )

        for command in import_config:
            # Insert placeholders
            command = self.interpolate_string(command)

            # Split string into its defined components
            into_section, path, from_section = command.split(' ')

            # Get the absolute path
            config_path = self.expand_path(Path(path))

            # Isert a ContextSectionImport tuple into the return value
            context_section_imports.append(
                ContextSectionImport(
                    into_section=into_section,
                    from_section=from_section,
                    from_config_file=config_path,
                )
            )

        return tuple(context_section_imports)


    def interpolate_string(self, string: str) -> str:
        """Replace all module placeholders in string."""
        string = string.format(
            # {period} -> current period defined by module timer
            period=self.timer.period(),
            # {name_of_template} -> string path to compiled template
            **{
                name: str(template['target'])
                for name, template
                in self.templates.items()
            }
        )
        return string

    @staticmethod
    def valid_class_section(section: ModuleConfig) -> bool:
        """Check if the given dict represents a valid enabled module."""

        if not len(section) == 1:
            raise RuntimeError(
                'Tried to check module section with dict '
                'which does not have exactly one item.',
            )

        try:
            module_name = next(iter(section.keys()))
            valid_module_name = module_name.split('/')[0] == 'module'  # type: ignore
            enabled = section[module_name].get('enabled', True)
            enabled = enabled not in (
                'false',
                'off',
                'disabled',
                'not',
                '0',
                False,
            )

            return valid_module_name and enabled
        except KeyError:
            return False

class ModuleManager:
    """A manager for operating on a set of modules."""

    def __init__(self, config: ApplicationConfig) -> None:
        self.application_config = config
        self.application_context = context(config)
        self.modules: Dict[str, Module] = {}
        self.startup_done = False
        self.last_module_periods: Dict[str, str] = {}

        for section, options in config.items():
            module_config = {section: options}
            if Module.valid_class_section(module_config):
                module = Module(
                    module_config=module_config,
                    config_directory=self.application_config['_runtime']['config_directory'],
                    temp_directory=self.application_config['_runtime']['temp_directory'],
                )
                self.modules[module.name] = module

    def __len__(self) -> int:
        """Return the number of managed modules."""
        return len(self.modules)

    def module_periods(self) -> Dict[str, str]:
        """Return dict containing the period of all modules."""
        module_periods = {}
        for module_name, module in self.modules.items():
            module_periods[module_name] = module.timer.period()

        return module_periods

    def finish_tasks(self) -> None:
        """
        Finish all due tasks defined by the managed modules.

        The order of finishing tasks is as follows:
            1) Import any relevant context sections.
            2) Compile all templates with the new section.
            3) Run startup commands, if it is not already done.
            4) Run period change commands, if it is not already done for this
               module periods combination.
        """
        if not self.startup_done:
            self.import_context_sections()
            self.compile_templates()
            self.startup()
            self.period_change()
        elif self.last_module_periods != self.module_periods():
            self.import_context_sections()
            self.compile_templates()
            self.period_change()

    def has_unfinished_tasks(self) -> bool:
        """Return True if there are any module tasks due."""
        if not self.startup_done:
            return True
        else:
            return self.last_module_periods != self.module_periods()

    def time_until_next_period(self) -> timedelta:
        """Time left until first period change of any of the modules managed."""
        return min(
            module.timer.time_until_next_period()
            for module
            in self.modules.values()
        )

    def import_context_sections(self):
        """Import context sections defined by the managed modules."""
        for module in self.modules.values():
            context_section_imports = module.context_section_imports()

            for csi in context_section_imports:
                self.application_context = insert_into(
                    context=self.application_context,
                    section=csi.into_section,
                    from_section=csi.from_section,
                    from_config_file=csi.from_config_file,
                )

    def compile_templates(self) -> None:
        """
        Compile the module templates specified by the `templates` option.
        """
        for module in self.modules.values():
            for files in module.templates.values():
                compiler.compile_template(
                    template=files['source'],
                    target=files['target'],
                    context=self.application_context,
                )

    def startup(self):
        """Run all startup commands specified by the managed modules."""
        for module in self.modules.values():
            startup_commands = module.startup_commands()
            for command in startup_commands:
                logger.info(f'[module/{module.name}] Running startup command.')
                self.run_shell(command, module.name)

        self.startup_done = True

    def period_change(self):
        """Run all period change commands specified by the managed modules."""
        for module in self.modules.values():
            period_change_commands = module.period_change_commands()
            for command in period_change_commands:
                logger.info(f'[module/{module.name}] Running period change command.')
                self.run_shell(command, module.name)

        self.last_module_periods = self.module_periods()

    def exit(self):
        """
        Run all exit commands specified by the managed modules.

        Also close all temporary file handlers created by the modules.
        """
        for module in self.modules.values():
            exit_commands = module.exit_commands()
            for command in exit_commands:
                logger.info(f'[module/{module.name}] Running exit command.')
                self.run_shell(command, module.name)

            if hasattr(module, 'temp_files'):
                for temp_file in module.temp_files:
                    temp_file.close()


    def run_shell(self, command: str, module_name: str) -> None:
        """Run a shell command defined by a managed module."""
        logger.info(f'[module/{module_name}] Running command "{command}".')
        run_shell(
            command=command,
            working_directory=self.application_config['_runtime']['config_directory'],
        )

