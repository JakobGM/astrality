"""Module implementing user configured custom functionality."""

from datetime import timedelta
import logging
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Dict, Iterable, List, Optional, Union

import compiler
from config import ApplicationConfig, insert_into
from resolver import Resolver
from timer import Timer, timer_factory
from utils import run_shell

ModuleConfig = Dict[str, Any]
logger = logging.getLogger('astrality')


class Module:
    """
    Class for executing user defined functionality in [module/*] section.

    The module can define a set of commands to be run on astrality startup, and
    exit, in addition to every time a given type of period changes.

    Commands are run in the users shell, and can use the following placeholders:
    - {period}: The period specified by the timer instance.
    - {name_of_template}: The path to the compiled template specified in the
                          'target' option.
    """

    def __init__(
        self,
        module_config: ModuleConfig,
        application_config: ApplicationConfig,
        manager: Optional['ModuleManager'] = None,
    ) -> None:
        """
        Initialize Module object with a section from a config dictionary.

        Argument `manager` is the ModuleManager instance responible for the
        Module instance, allowing two-way communication between modules and
        their respective managers.

        Section name must be [module/*], where * is the module name.
        In addition, the enabled option must be set to "true", or not set at
        all.
        """
        self.manager: Optional['ModuleManager'] = manager
        self.application_config: ApplicationConfig = application_config  # type: ignore

        if self.manager:
            self.application_config = self.manager.application_config

        section = next(iter(module_config.keys()))
        self.name: str = section.split('/')[1]  # type: ignore

        self.config: ModuleConfig = module_config[section]

        # Use static timer if no timer is specified
        self.timer: Timer = timer_factory(
            self.config.get('timer', {'type': 'static'}),
        )

        # Commands to run at specified times
        self.startup_commands: List[str] = self.config.get('run_on_startup', [])
        self.period_change_commands: List[str] = self.config.get('run_on_period_change', [])
        self.exit_commands: List[str] = self.config.get('run_on_exit', [])
        self.import_sections_on_period_change: List[str] = self.config.get('import_sections_on_period_change', [])

        # Attributes used in order to keep track of unfinished tasks
        self.startup_commands_have_been_run = False
        self.last_period_change_run = 'this_period_should_never_be_valid'
        self.last_compilation_period = 'this_period_should_never_be_valid'

        # Find and prepare templates and compilation targets
        self._prepare_templates()

    def _prepare_templates(self) -> None:
        """Determine template sources and compilation targets."""

        # config['templates'] is a dictionary with keys naming each template,
        # and values containing another dictionary containing the mandatory
        # key `source`, and the optional key `target`.
        templates: Dict[str, Dict[str, str]] = self.config.get(
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
            dir=self.application_config['_runtime']['temp_directory'],
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
                self.application_config['_runtime']['config_directory'],
                path,
            )

        return path

    def startup(self) -> None:
        """Commands to be run on Module instance startup."""

        self.startup_commands_have_been_run = True

        self.compile_templates()

        for command in self.startup_commands:
            logger.info(f'[module/{self.name}] Running startup command.')
            self.run_shell(command=command)

        if len(self.startup_commands) == 0:
            logger.debug(f'[module/{self.name}] No startup command specified.')

    def period_change(self) -> None:
        """Commands to be run when self.timer period changes."""

        self.last_period_change_run = self.timer.period()

        self.compile_templates()

        for command in self.period_change_commands:
            logger.info(f'[module/{self.name}] Running period change command.')
            self.run_shell(command=command)

        if len(self.period_change_commands) == 0:
            logger.debug(f'[module/{self.name}] No period change command specified.')

    def exit(self) -> None:
        """Commands to be run on Module instance shutdown."""

        for command in self.exit_commands:
            logger.info(f'[module/{self.name}] Running exit command.')
            self.run_shell(command=command)

        if len(self.exit_commands) == 0:
            logger.debug(f'[module/{self.name}] No exit command specified.')

        if hasattr(self, 'temp_files'):
            # Temporary files have been created for this module and they should
            # be deleted.
            for temp_file in self.temp_files:
                temp_file.close()

    def has_unfinished_tasks(self) -> bool:
        """Returns True if any of the modules have unfinished tasks."""

        return not self.startup_commands_have_been_run or \
            self.last_period_change_run != self.timer.period()

    def finish_tasks(self) -> None:
        """Finish all unfinished tasks of all the modules."""

        if not self.startup_commands_have_been_run:
            self.startup()

        if self.last_period_change_run != self.timer.period():
            self.period_change()

            if len(self.import_sections_on_period_change) != 0:
                for command in self.import_sections_on_period_change:
                    self.import_section(command)

                if self.manager:
                    for module in self.manager.modules:
                        module.compile_templates(force=True)

    def compile_templates(self, force=False) -> None:
        """
        Compile the module templates specified by the `templates` option.

        If force=True, the template files will be compiled even though the
        period has not changed since the last compilation. This is used when
        some module has changed the application config by importing a new
        section, which requires recompilation of all templates to reflect the
        new changes to the application config.
        """

        period = self.timer.period()

        if force or self.last_compilation_period != period:
            # The period has changed, and there is a need for compiling the
            # templates again with the new period.
            self.last_compilation_period = period

            for name, template in self.templates.items():
                compiler.compile_template(
                    template=template['source'],
                    target=template['target'],
                    context=self.application_config,
                )

    def run_shell(self, command) -> None:
        command = command.format(
            period=self.timer.period(),
            **{
                name: template['target']
                for name, template
                in self.templates.items()
            }
        )
        logger.info(f'[module/{self.name}] Running command "{command}".')
        run_shell(
            command=command,
            working_directory=self.application_config['_runtime']['config_directory'],
        )

    def import_section(self, command: str) -> None:
        """Import config section into application config."""
        section, path, from_section = command.format(
            period=self.timer.period(),
        ).split(' ')
        config_path = self.expand_path(Path(path))

        insert_into(
            config=self.application_config,
            section=section,
            from_config_file=config_path,
            from_section=from_section,
        )

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
        self.modules: List[Module] = []

        for section, options in config.items():
            module_resolver = {section: options}
            if Module.valid_class_section(module_resolver):
                self.modules.append(Module(
                    module_config=module_resolver,
                    application_config=self.application_config,
                    manager=self,
                ))

    def __len__(self) -> int:
        """Return the number of managed modules."""

        return len(self.modules)

    def time_until_next_period(self) -> timedelta:
        """Time left until first period change of any of the modules managed."""

        return min(
            module.timer.time_until_next_period()
            for module
            in self.modules
        )

    def has_unfinished_tasks(self) -> bool:
        return any(
            module.has_unfinished_tasks()
            for module
            in self.modules
        )

    def modules_with_unfinished_tasks(self) -> Iterable[Module]:
        """Return a generator of all modules with unfinished tasks."""

        return (
            module
            for module
            in self.modules
            if module.has_unfinished_tasks()
        )

    def finish_tasks(self) -> None:
        """Finish all unfinished tasks of all the managed modules."""

        for module in self.modules_with_unfinished_tasks():
            module.finish_tasks()

    def exit(self) -> None:
        """Run all module on_exit commands."""

        logger.info('Running all module on_exit commands')

        for module in self.modules:
            try:
                module.exit()
            except FileNotFoundError:
                # Some temp file has already been cleaned up.
                # This shouldn't be necessary if we are more careful with
                # keeping 'TemporaryFile's within scope, but alas, it is what
                # it is at the moment. I think this exception may be caused
                # by running tests at the same time Astrality is interrupted.
                continue
