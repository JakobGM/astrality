"""Module implementing user configured custom functionality."""

import logging
from collections import defaultdict
from datetime import timedelta
from pathlib import Path
import re
from typing import (
    Callable,
    DefaultDict,
    Dict,
    Iterable,
    List,
    Match,
    Optional,
    Set,
    Tuple,
    Union,
)

from mypy_extensions import TypedDict

from astrality import compiler
from astrality.actions import ActionBlock, ActionBlockDict
from astrality.compiler import context
from astrality.config import (
    ApplicationConfig,
    GlobalModulesConfig,
    expand_path,
    user_configuration,
)
from astrality.event_listener import (
    EventListener,
    EventListenerConfig,
    event_listener_factory,
)
from astrality.filewatcher import DirectoryWatcher
from astrality.resolver import Resolver
from astrality.requirements import Requirement, RequirementDict
from astrality.utils import cast_to_list


class ModuleConfigDict(TypedDict, total=False):
    """Content of module configuration dict."""

    enabled: Optional[bool]
    requires: Union[RequirementDict, List[RequirementDict]]
    event_listener: EventListenerConfig

    on_startup: ActionBlockDict
    on_exit: ActionBlockDict
    on_event: ActionBlockDict
    on_modified: Dict[str, ActionBlockDict]


class ModuleActionBlocks(TypedDict):
    """Contents of Module().action_blocks."""

    on_startup: ActionBlock
    on_event: ActionBlock
    on_exit: ActionBlock
    on_modified: Dict[Path, ActionBlock]


ModuleConfig = Dict[str, ModuleConfigDict]
logger = logging.getLogger('astrality')


class Module:
    """
    Class for determining module actions.

    A Module instance should only return actions to be performed, but never
    perform them. That is the responsibility of a ModuleManager instance.

    A module can define a set of commands to be run on astrality startup, and
    exit, in addition to every time a given type of event changes.

    Commands are run in the users shell, and can use the following placeholder:
    - {event}: The event specified by the event_listener instance.

    :param module_config: Dictionary keyed to module name and containing all
        module options.
    :param module_directory: The directory which contains all module relevant
        files, such as `config.yml`. All relative paths use this as anchor.
    :param replacer: String options should be processed by this function in
        order to replace relevant placeholders.
    """

    action_blocks: ModuleActionBlocks

    def __init__(
        self,
        module_config: ModuleConfig,
        module_directory: Path,
        replacer: Callable[[str], str] = lambda string: string,
        context_store: compiler.Context = {},
    ) -> None:
        """
        Initialize Module object with a section from a config dictionary.

        Section name must be [module/*], where * is the module name.
        In addition, the enabled option must be set to "true", or not set at
        all.

        module_config example:
        {'module/name':
            'enabled': True,
            'event_listener': {'type': 'weekday'},
            'on_startup': {'run': ['echo weekday is {event}']},
        }
        """
        # Can only initialize one module at a time
        assert len(module_config) == 1

        section: str = next(iter(module_config.keys()))
        self.name: str = section[7:]

        # The source directory for the module, determining how to interpret
        # relative paths in the module config
        self.directory = module_directory

        # All user string options should be processed by the replacer
        self.replace = replacer

        # Extract configuration content
        module_config_content: ModuleConfigDict = module_config[section]

        # Use static event_listener if no event_listener is specified
        self.event_listener: EventListener = \
            event_listener_factory(
                module_config_content.get(
                    'event_listener',
                    {'type': 'static'},
                ),
            )

        self.context_store = context_store

        # Create action block object for each available action block type
        action_blocks: ModuleActionBlocks = {'on_modified': {}}  # type: ignore
        for block_name in ('on_startup', 'on_event', 'on_exit'):
            action_blocks[block_name] = ActionBlock(  # type: ignore
                action_block=module_config_content.get(  # type: ignore
                    block_name,
                    {},
                ),
                directory=self.directory,
                replacer=self.interpolate_string,
                context_store=self.context_store,
            )
        for path_string, action_block_dict \
                in module_config_content.get('on_modified', {}).items():
            modified_path = expand_path(
                path=Path(path_string),
                config_directory=self.directory,
            )
            action_blocks['on_modified'][modified_path] = ActionBlock(
                action_block=action_block_dict,
                directory=self.directory,
                replacer=self.interpolate_string,
                context_store=self.context_store,
            )
        self.action_blocks = action_blocks

    def get_action_block(
        self,
        name: str,
        path: Optional[Path] = None,
    ) -> ActionBlock:
        """
        Return specific action block from module.

        :param name: Identifier of action block, for example 'on_startup'.
        :param path: If `name` == on_modified, path specifies modified path.
        """
        if path:
            assert path.is_absolute()
            assert name == 'on_modified'
            return self.action_blocks[name][path]  # type: ignore
        else:
            assert name in ('on_startup', 'on_event', 'on_exit',)
            return self.action_blocks[name]  # type: ignore

    def import_context(
        self,
        block_name: str,
        path: Optional[Path] = None,
    ) -> None:
        """
        Execute all import context actions specified in block_name[:path].

        :param block_name: Name of block such as 'on_startup'.
        :param path: Absolute path in case of block_name == 'on_modified'.
        """
        action_block = self.get_action_block(name=block_name, path=path)
        action_block.import_context()

        # Import context sections from triggered action blocks
        triggers = action_block.triggers()
        for trigger in triggers:
            self.import_context(
                block_name=trigger.block,
                path=trigger.absolute_path,
            )

    def symlink(
        self,
        block_name: str,
        path: Optional[Path] = None,
    ) -> None:
        """
        Execute all symlink actions specified in block_name[:path].

        :param block_name: Name of block such as 'on_startup'.
        :param path: Absolute path in case of block_name == 'on_modified'.
        """
        action_block = self.get_action_block(name=block_name, path=path)
        action_block.symlink()

        # Symlink from triggered action blocks
        triggers = action_block.triggers()
        for trigger in triggers:
            self.symlink(
                block_name=trigger.block,
                path=trigger.absolute_path,
            )

    def copy(
        self,
        block_name: str,
        path: Optional[Path] = None,
    ) -> None:
        """
        Execute all copy actions specified in block_name[:path].

        :param block_name: Name of block such as 'on_startup'.
        :param path: Absolute path in case of block_name == 'on_modified'.
        """
        action_block = self.get_action_block(name=block_name, path=path)
        action_block.copy()

        # Symlink from triggered action blocks
        triggers = action_block.triggers()
        for trigger in triggers:
            self.copy(
                block_name=trigger.block,
                path=trigger.absolute_path,
            )

    def compile(
        self,
        block_name: str,
        path: Optional[Path] = None,
    ) -> None:
        """
        Execute all compile actions specified in block_name[:path].

        :param block_name: Name of block such as 'on_startup'.
        :param path: Absolute path in case of block_name == 'on_modified'.
        """
        action_block = self.get_action_block(name=block_name, path=path)
        action_block.compile()

        # Compile templates from triggered action blocks
        triggers = action_block.triggers()
        for trigger in triggers:
            self.compile(
                block_name=trigger.block,
                path=trigger.absolute_path,
            )

    def stow(
        self,
        block_name: str,
        path: Optional[Path] = None,
    ) -> None:
        """
        Execute all stow actions specified in block_name[:path].

        :param block_name: Name of block such as 'on_startup'.
        :param path: Absolute path in case of block_name == 'on_modified'.
        """
        action_block = self.get_action_block(name=block_name, path=path)
        action_block.stow()

        # Symlink from triggered action blocks
        triggers = action_block.triggers()
        for trigger in triggers:
            self.stow(
                block_name=trigger.block,
                path=trigger.absolute_path,
            )

    def run(
        self,
        block_name: str,
        default_timeout: Union[int, float],
        path: Optional[Path] = None,
    ) -> Tuple[Tuple[str, str], ...]:
        """
        Execute all run actions specified in block_name[:path].

        :param block_name: Name of block such as 'on_startup'.
        :param default_timeout: Default timeout for run actions.
        :param path: Absolute path in case of block_name == 'on_modified'.
        """
        action_block = self.get_action_block(name=block_name, path=path)
        results = action_block.run(default_timeout=default_timeout)

        # Run shell commands from triggered action blocks
        triggers = action_block.triggers()
        for trigger in triggers:
            new_results = self.run(
                block_name=trigger.block,
                default_timeout=default_timeout,
                path=trigger.absolute_path,
            )
            if new_results:
                results += new_results

        return results

    def all_action_blocks(self) -> Iterable[ActionBlock]:
        """Return flatten tuple of all module action blocks."""
        return (
            self.action_blocks['on_startup'],
            self.action_blocks['on_event'],
            self.action_blocks['on_exit'],
            *self.action_blocks['on_modified'].values(),
        )

    def performed_compilations(self) -> DefaultDict[Path, Set[Path]]:
        """
        Return all templates that have been compiled and their target(s).

        :return: Dictionary with template path keys and values as a set of
            compilation target paths for that template.
        """
        performed_compilations: DefaultDict[Path, Set[Path]] = defaultdict(set)
        for action_block in self.all_action_blocks():
            for template, targets \
                    in action_block.performed_compilations().items():
                performed_compilations[template] |= targets

        return performed_compilations

    def interpolate_string(self, string: str) -> str:
        """
        Replace all module placeholders in string.

        The configuration string processor replaces {event} with the current
        module event, and {/path/to/template} with the compilation target.

        :return: String where '{path/to/template}' has been replaced with
            'path/to/compilation/target', and {event} repleced with last event.
        """
        # First replace any event placeholders with the last event, this must
        # be done before path replacements as paths could contain {event}.
        string = self.replace(
            string.replace(
                '{event}',
                self.event_listener.event(),
            ),
        )

        placeholder_pattern = re.compile(r'({.+})')
        performed_compilations = self.performed_compilations()

        def replace_placeholders(match: Match) -> str:
            """Regex file path match replacer."""
            # Remove enclosing curly brackets
            specified_path = match.group(0)[1:-1]

            absolute_path = expand_path(
                path=Path(specified_path),
                config_directory=self.directory,
            )

            if absolute_path in performed_compilations:
                # TODO: Is joining the right thing to do here?
                return " ".join(
                    [
                        str(path)
                        for path
                        in performed_compilations[absolute_path]
                    ],
                )
            else:
                logger.error(
                    'String placeholder {' + specified_path + '} '
                    f'could not be replaced. "{specified_path}" '
                    'has not been compiled.',
                )
                # Return the placeholder left alone
                return '{' + specified_path + '}'

        return placeholder_pattern.sub(
            repl=replace_placeholders,
            string=string,
        )

    @staticmethod
    def valid_class_section(
        section: ModuleConfig,
        requires_timeout: Union[int, float],
        requires_working_directory: Path,
    ) -> bool:
        """Check if the given dict represents a valid enabled module."""
        if not len(section) == 1:
            raise RuntimeError(
                'Tried to check module section with dict '
                'which does not have exactly one item.',
            )

        try:
            module_name = next(iter(section.keys()))
            valid_module_name = \
                module_name.split('/')[0].lower() == 'module'  # type: ignore
            enabled = section[module_name].get('enabled', True)
            if not (valid_module_name and enabled):
                return False

        except KeyError:
            return False

        # The module is enabled, now check if all requirements are satisfied
        requires: List[RequirementDict] = cast_to_list(
            section[module_name].get(
                'requires',
                {},
            ),
        )
        requirements = [
            Requirement(
                requirements=requirements_dict,
                directory=requires_working_directory,
                timeout=requires_timeout,
            )
            for requirements_dict
            in requires
        ]
        if all(requirements):
            return True
        else:
            logger.warning(
                f'[{module_name}] ' +
                ", ".join([
                    repr(requirement)
                    for requirement
                    in requirements
                ]) + '!',
            )
            return False


class ModuleManager:
    """A manager for operating on a set of modules."""

    def __init__(self, config: ApplicationConfig) -> None:
        """Initialize a ModuleManager object from `astrality.yml` dict."""
        self.config_directory = Path(config['_runtime']['config_directory'])
        self.temp_directory = Path(config['_runtime']['temp_directory'])
        self.application_config = config
        self.application_context: Dict[str, Resolver] = {}

        self.startup_done = False
        self.last_module_events: Dict[str, str] = {}

        # Get module configurations which are externally defined
        self.global_modules_config = GlobalModulesConfig(  # type: ignore
            config=config.get('config/modules', {}),
            config_directory=self.config_directory,
        )
        self.reprocess_modified_files = \
            self.global_modules_config.reprocess_modified_files

        self.modules: Dict[str, Module] = {}

        # Application context is used in compiling external config sources
        application_context = context(config)

        # Insert externally managed modules
        for external_module_source \
                in self.global_modules_config.external_module_sources:
            module_directory = external_module_source.directory

            module_configs = external_module_source.config(
                context=application_context,
            )

            # Insert context defined in external configuration
            self.application_context.update(context(module_configs))

            for section, options in module_configs.items():
                module_config = {section: options}

                if not Module.valid_class_section(
                    section=module_config,
                    requires_timeout=self.global_modules_config.requires_timeout,  # noqa
                    requires_working_directory=module_directory,
                ) or section not in self.global_modules_config.enabled_modules:
                    continue

                module = Module(
                    module_config=module_config,
                    module_directory=module_directory,
                    replacer=self.interpolate_string,
                    context_store=self.application_context,
                )
                self.modules[module.name] = module

        # Update the context from `astrality.yml`, overwriting any defined
        # contexts in external modules in the case of naming conflicts
        self.application_context.update(application_context)

        # Insert modules defined in `astrality.yml`
        for section, options in config.items():
            module_config = {section: options}

            # Check if this module should be included
            if not Module.valid_class_section(
                section=module_config,
                requires_timeout=self.global_modules_config.requires_timeout,
                requires_working_directory=self.config_directory,
            ) or section not in self.global_modules_config.enabled_modules:
                continue

            module = Module(
                module_config=module_config,
                module_directory=self.config_directory,
                replacer=self.interpolate_string,
                context_store=self.application_context,
            )
            self.modules[module.name] = module

        # Initialize the config directory watcher, but don't start it yet
        self.directory_watcher = DirectoryWatcher(
            directory=self.config_directory,
            on_modified=self.file_system_modified,
        )

        logger.info('Enabled modules: ' + ', '.join(self.modules.keys()))

    def __len__(self) -> int:
        """Return the number of managed modules."""
        return len(self.modules)

    def module_events(self) -> Dict[str, str]:
        """Return dict containing the event of all modules."""
        module_events = {}
        for module_name, module in self.modules.items():
            module_events[module_name] = module.event_listener.event()

        return module_events

    def finish_tasks(self) -> None:
        """
        Finish all due tasks defined by the managed modules.

        The order of finishing tasks is as follows:
            1) Import any relevant context sections.
            2) Compile all templates with the new section.
            3) Run startup commands, if it is not already done.
            4) Run on_event commands, if it is not already done for this
               module events combination.
        """
        if not self.startup_done:
            # Save the last event configuration, such that on_event
            # is only run when the event *changes*
            self.last_module_events = self.module_events()

            # Perform all startup actions
            self.startup()
        elif self.last_module_events != self.module_events():
            # One or more module events have changed, execute the event blocks
            # of these modules.

            for module_name, event in self.module_events().items():
                if not self.last_module_events[module_name] == event:
                    # This module has a new event

                    self.import_context_sections(
                        trigger='on_event',
                        module=self.modules[module_name],
                    )
                    self.compile_templates(
                        trigger='on_event',
                        module=self.modules[module_name],
                    )
                    self.run_on_event_commands(
                        module=self.modules[module_name],
                    )

                    # Save the event
                    self.last_module_events[module_name] = event

    def has_unfinished_tasks(self) -> bool:
        """Return True if there are any module tasks due."""
        if not self.startup_done:
            return True
        else:
            return self.last_module_events != self.module_events()

    def time_until_next_event(self) -> timedelta:
        """Time left until first event change of any of the modules managed."""
        return min(
            module.event_listener.time_until_next_event()
            for module
            in self.modules.values()
        )

    def import_context_sections(
        self,
        trigger: str,
        module: Optional[Module] = None,
    ) -> None:
        """
        Import context sections defined by the managed modules.

        Trigger is one of 'on_startup', 'on_event', or 'on_exit'.
        This determines which event block of the module is used to get the
        context import specification from.
        """
        assert trigger in ('on_startup', 'on_event', 'on_exit',)

        modules: Iterable[Module]
        if isinstance(module, Module):
            modules = (module, )
        else:
            modules = self.modules.values()

        for module in modules:
            module.import_context(block_name=trigger)

    def compile_templates(
        self,
        trigger: str,
        module: Optional[Module] = None,
    ) -> None:
        """
        Compile the module templates specified by the `templates` option.

        Trigger is one of 'on_startup', 'on_event', or 'on_exit'.
        This determines which section of the module is used to get the compile
        specification from.
        """
        assert trigger in ('on_startup', 'on_event', 'on_exit',)

        modules: Iterable[Module]
        if isinstance(module, Module):
            modules = (module, )
        else:
            modules = self.modules.values()

        for module in modules:
            module.compile(block_name=trigger)

    def startup(self):
        """Run all startup actions specified by the managed modules."""
        assert not self.startup_done

        self.import_context_sections('on_startup')
        self.compile_templates('on_startup')

        for module in self.modules.values():
            logger.info(f'[module/{module.name}] Running startup commands.')
            module.run(
                block_name='on_startup',
                default_timeout=self.global_modules_config.run_timeout,
            )

        self.startup_done = True

        # Start watching config directory for file changes
        self.directory_watcher.start()

    def run_on_event_commands(
        self,
        module: Module,
    ):
        """Run all event change commands specified by a managed module."""
        logger.info(f'[module/{module.name}] Running event commands.')
        module.run(
            block_name='on_event',
            default_timeout=self.global_modules_config.run_timeout,
        )

    def exit(self):
        """
        Run all exit tasks specified by the managed modules.

        Also close all temporary file handlers created by the modules.
        """
        # First import context and compile templates
        self.import_context_sections('on_exit')
        self.compile_templates('on_exit')

        # Then run all shell commands
        for module in self.modules.values():
            logger.info(f'[module/{module.name}] Running exit commands.')
            module.run(
                block_name='on_exit',
                default_timeout=self.global_modules_config.run_timeout,
            )

        if hasattr(self, 'temp_files'):
            for temp_file in self.temp_files:
                temp_file.close()

            # Prevent files from being closed again
            del self.temp_files

        # Stop watching config directory for file changes
        self.directory_watcher.stop()

    def on_modified(self, modified: Path) -> bool:
        """
        Perform actions when a watched file is modified.

        :return: Returns True if on_modified block was triggered.
        """
        assert modified.is_absolute()
        triggered = False

        for module in self.modules.values():
            if modified not in module.action_blocks['on_modified']:
                continue

            triggered = True
            logger.info(
                f'[module/{module.name}] on_modified:{modified} triggered.',
            )

            # First import context sections in on_modified block
            module.import_context(block_name='on_modified', path=modified)

            # Now compile templates specified in on_modified block
            module.compile(block_name='on_modified', path=modified)

            # Lastly, run commands specified in on_modified block
            logger.info(f'[module/{module.name}] Running modified commands.')
            module.run(
                'on_modified',
                path=modified,
                default_timeout=self.global_modules_config.run_timeout,
            )

        return triggered

    def file_system_modified(self, modified: Path) -> None:
        """
        Perform actions for when files within the config directory are modified.

        Run any context imports, compilations, and shell commands specified
        within the on_modified event block of each module.

        Also, if hot_reload is True, we reinstantiate the ModuleManager object
        if the application configuration has been modified.
        """
        config_file = \
            self.application_config['_runtime']['config_directory'] \
            / 'astrality.yml'

        if modified == config_file:
            self.on_application_config_modified()
            return
        else:
            # Run any relevant on_modified blocks.
            triggered = self.on_modified(modified)

        if not triggered:
            # Check if the modified path is a template which is supposed to
            # be recompiled.
            self.recompile_modified_template(modified=modified)

    def on_application_config_modified(self):
        """
        Reload the ModuleManager if astrality.yml has been modified.

        Reloadnig the module manager only occurs if the user has configured
        `hot_reload_config`.
        """
        if not self.application_config['config/astrality']['hot_reload_config']:
            # Hot reloading is not enabled, so we return early
            return

        # Hot reloading is enabled, get the new configuration dict
        new_application_config = user_configuration(
            config_directory=self.config_directory,
        )

        try:
            # Reinstantiate this object
            new_module_manager = ModuleManager(new_application_config)

            # Run all old exit actions, since the new config is valid
            self.exit()

            # Swap place with the new configuration
            self = new_module_manager

            # Run startup commands from the new configuration
            self.finish_tasks()
        except Exception:
            # New configuration is invalid, just keep the old one
            # TODO: Test this behaviour
            logger.error('New configuration detected, but it is invalid!')
            pass

    def recompile_modified_template(self, modified: Path):
        """
        Recompile any modified template if configured.

        This requires setting the global setting:
        reprocess_modified_files: true
        """
        if not self.reprocess_modified_files:
            return

        # Run any compile action a new if that compile action uses the modifed
        # path as a template.
        for module in self.modules.values():
            for action_block in module.all_action_blocks():
                for compile_action in action_block._compile_actions:
                    if modified in compile_action:
                        compile_action.execute()

    def interpolate_string(self, string: str) -> str:
        """
        Process configuration string before using it.

        This function is passed as a reference to all modules, making them
        perform the replacement instead. For now, the ModuleManager does not
        change the string at all, but we will leave it here in case we would
        want to interpolate strings from the ModuleManager level instead of
        the Module level.

        :param string: String to be processed.
        :return: Processed string.
        """
        return string
