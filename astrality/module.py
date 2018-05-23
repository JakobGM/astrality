"""Module implementing user configured custom functionality."""

import logging
from collections import defaultdict
from datetime import timedelta
from pathlib import Path
import psutil
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

from astrality.actions import ActionBlock, ActionBlockDict, SetupActionBlock
from astrality.config import (
    AstralityYAMLConfigDict,
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
from astrality.context import Context
from astrality.requirements import Requirement, RequirementDict
from astrality.utils import cast_to_list


class ModuleConfigDict(TypedDict, total=False):
    """Content of module configuration dict."""

    enabled: Optional[bool]
    requires: Union[RequirementDict, List[RequirementDict]]
    event_listener: EventListenerConfig

    on_setup: ActionBlockDict
    on_startup: ActionBlockDict
    on_exit: ActionBlockDict
    on_event: ActionBlockDict
    on_modified: Dict[str, ActionBlockDict]


class ModuleActionBlocks(TypedDict):
    """Contents of Module().action_blocks."""

    on_setup: SetupActionBlock
    on_startup: ActionBlock
    on_event: ActionBlock
    on_exit: ActionBlock
    on_modified: Dict[Path, ActionBlock]


logger = logging.getLogger(__name__)


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
    :param global_modules_config: GlobalModulesConfig object specifying
        configuration options applicable to all modules, such as run_timeout.
    :param dry_run: If file system actions should be printed and skipped.
    """

    action_blocks: ModuleActionBlocks
    depends_on: Tuple[str]

    def __init__(
        self,
        name: str,
        module_config: ModuleConfigDict,
        module_directory: Path,
        replacer: Callable[[str], str] = lambda string: string,
        context_store: Context = Context(),
        global_modules_config: Optional[GlobalModulesConfig] = None,
        dry_run: bool = False,
    ) -> None:
        """
        Initialize Module object with a section from a config dictionary.

        Section name must be [module/*], where * is the module name.
        In addition, the enabled option must be set to "true", or not set at
        all.

        module_config example:
        {'name':
            'enabled': True,
            'event_listener': {'type': 'weekday'},
            'on_startup': {'run': ['echo weekday is {event}']},
        }
        """
        self.name = name

        # The source directory for the module, determining how to interpret
        # relative paths in the module config
        self.directory = module_directory

        # All user string options should be processed by the replacer
        self.replace = replacer

        # Use static event_listener if no event_listener is specified
        self.event_listener: EventListener = \
            event_listener_factory(
                module_config.get(
                    'event_listener',
                    {'type': 'static'},
                ),
            )

        self.context_store = context_store

        # Move root actions to 'on_startup' block
        module_config = self.prepare_on_startup_block(
            module_name=self.name,
            module_config=module_config,
        )

        # Create action block object for each available action block type
        action_blocks: ModuleActionBlocks = {'on_modified': {}}  # type: ignore
        params = {
            'module_name': self.name,
            'directory': self.directory,
            'replacer': self.interpolate_string,
            'context_store': self.context_store,
            'global_modules_config': global_modules_config,
        }

        # Create special case setup action block, it removes any action already
        # performed.
        action_blocks['on_setup'] = SetupActionBlock(  # type: ignore
            action_block=module_config.get('on_setup', {}),
            **params,
        )

        # Create normal action blocks
        for block_name in ('on_startup', 'on_event', 'on_exit'):
            action_blocks[block_name] = ActionBlock(  # type: ignore
                action_block=module_config.get(  # type: ignore
                    block_name,
                    {},
                ),
                **params,
            )

        for path_string, action_block_dict in module_config.get(
            'on_modified',
            {},
        ).items():
            modified_path = expand_path(
                path=Path(path_string),
                config_directory=self.directory,
            )
            action_blocks['on_modified'][modified_path] = \
                ActionBlock(  # type: ignore
                    action_block=action_block_dict,
                    **params,
            )

        self.action_blocks = action_blocks

        requirements = cast_to_list(module_config.get('requires', []))
        self.depends_on = tuple(  # type: ignore
            requirement['module']
            for requirement
            in requirements
            if 'module' in requirement
        )

    @staticmethod
    def prepare_on_startup_block(
        module_name: str,
        module_config: ModuleConfigDict,
    ) -> ModuleConfigDict:
        """
        Move actions at root indentation to on_startup block.

        NB! Mutates module_config in-place.

        :param module_config: Module configuration dictionary.
        :return: Configuration dictionary with root actions moved to on_startup.
        """
        action_types = ActionBlock.action_types.keys()
        root_level_action_types = [
            action_type
            for action_type
            in action_types
            if action_type in module_config
        ]

        if not root_level_action_types:
            return module_config

        if 'on_startup' in module_config:
            logger.error(
                f'[module/{module_name}] Actions defined both at root '
                'indentation and in "on_startup" block. This is reduntant! '
                'Root action types might overwrite "on_startup" actions.',
            )
        else:
            module_config['on_startup'] = {}

        for action_type in root_level_action_types:
            module_config[
                'on_startup'
            ][action_type] = module_config.pop(action_type)  # type: ignore

        return module_config

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
            assert name in ('on_setup', 'on_startup', 'on_event', 'on_exit')
            return self.action_blocks[name]  # type: ignore

    def execute(
        self,
        action: str,
        block: str,
        path: Optional[Path] = None,
        dry_run: bool = False,
    ) -> Optional[Tuple[Tuple[str, str], ...]]:
        """
        Perform action defined in action block.

        :param actions: Action type to be performed such as 'compile'.
            If passed 'all' then all actions types will be triggered.
        :param block_name: Name of block such as 'on_startup'.
        :param path: Absolute path in case of block_name == 'on_modified'.
        :param dry_run: If external side-effects should be skipped.
        :return: Optional tuple of 2-tuples if run actions have been performed.
            First item is command being run, second item is the standard output
            of the shell command.
        """
        if action == 'all':
            # If 'all' is specified, then we can run all actions except trigger,
            # as triggers are handled in each respective action.
            all_actions = filter(
                lambda x: x != 'trigger',
                ActionBlock.action_types.keys(),
            )

            results: Tuple[Tuple[str, str], ...] = tuple()
            for action in all_actions:
                result = self.execute(
                    action=action,
                    block=block,
                    path=path,
                    dry_run=dry_run,
                )
                if result:
                    results += result

            return results

        # In this branch, we have a single action, for example 'run'.
        assert isinstance(action, str)
        assert action in ActionBlock.action_types
        action_block = self.get_action_block(name=block, path=path)
        results = getattr(action_block, action)(dry_run=dry_run)

        # We need to execute the same action in any triggered action block
        triggers = action_block.triggers()
        for trigger in triggers:
            result = self.execute(
                action=action,
                block=trigger.block,
                path=trigger.absolute_path,
                dry_run=dry_run,
            )
            if result:
                results += result

        return results

    def all_action_blocks(self) -> Iterable[ActionBlock]:
        """Return flatten tuple of all module action blocks."""
        return (
            self.action_blocks['on_setup'],
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
                return ' '.join(
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

    @property
    def keep_running(self) -> bool:
        """Return True if Module needs to keep running."""
        on_modifed = bool(self.action_blocks['on_modified'])
        event_listener = bool(self.action_blocks['on_event']) \
            and self.event_listener.type_ != 'static'

        return on_modifed or event_listener

    def __repr__(self) -> str:
        """Return string representation of Module object."""
        return f'Module(name={self.name})'

    @staticmethod
    def valid_module(
        name: str,
        config: ModuleConfigDict,
        requires_timeout: Union[int, float],
        requires_working_directory: Path,
    ) -> bool:
        """
        Check if the given dict represents a valid enabled module.

        The method determines this by inspecting any requires items the module
        might have specified.

        :param name: Name of module, used for logging purposes.
        :param config: Configuration dictionary of the module.
        :param requires_timeout: Time to wait for shell command requirements.
        :param requires_working_directory: CWD for shell commands.
        :return: True if module should be enabled.
        """
        if not config.get('enabled', True):
            return False

        # The module is enabled, now check if all requirements are satisfied
        requires: List[RequirementDict] = cast_to_list(
            config.get(
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
                f'[module/{name}] ' +
                ', '.join([
                    repr(requirement)
                    for requirement
                    in requirements
                ]) + '!',
            )
            return False


class ModuleManager:
    """
    A manager for operating on a set of modules.

    :param config: Global configuration options.
    :param modules: Dictionary containing globally defined modules.
    :param context: Global context.
    :param directory: Directory containing global configuration.
    :param dry_run: If file system actions should be printed and skipped.
    """

    def __init__(
        self,
        config: AstralityYAMLConfigDict = {},
        modules: Dict[str, ModuleConfigDict] = {},
        context: Context = Context(),
        directory: Path = Path(__file__).parent / 'tests' / 'test_config',
        dry_run: bool = False,
    ) -> None:
        """Initialize a ModuleManager object from `astrality.yml` dict."""
        self.config_directory = directory
        self.application_config = config
        self.application_context = context
        self.dry_run = dry_run

        self.startup_done = False
        self.last_module_events: Dict[str, str] = {}

        # Get module configurations which are externally defined
        self.global_modules_config = GlobalModulesConfig(
            config=config.get('modules', {}),
            config_directory=self.config_directory,
        )
        self.reprocess_modified_files = \
            self.global_modules_config.reprocess_modified_files

        self.modules: Dict[str, Module] = {}

        # Insert externally managed modules
        for external_module_source \
                in self.global_modules_config.external_module_sources:
            # Insert context defined in external configuration
            module_context = external_module_source.context(
                context=self.application_context,
            )
            self.application_context.reverse_update(module_context)

            module_configs = external_module_source.modules(
                context=self.application_context,
            )
            module_directory = external_module_source.directory

            for module_name, module_config in module_configs.items():
                if module_name \
                        not in self.global_modules_config.enabled_modules:
                    continue

                if not Module.valid_module(
                    name=module_name,
                    config=module_config,
                    requires_timeout=self.global_modules_config.
                    requires_timeout,  # noqa
                    requires_working_directory=module_directory,
                ):
                    continue

                module = Module(
                    name=module_name,
                    module_config=module_config,
                    module_directory=module_directory,
                    replacer=self.interpolate_string,
                    context_store=self.application_context,
                    global_modules_config=self.global_modules_config,
                    dry_run=dry_run,
                )
                self.modules[module.name] = module

        # Insert modules defined in `astrality.yml`
        for module_name, module_config in modules.items():
            # Check if this module should be included
            if module_name not in self.global_modules_config.enabled_modules:
                continue

            if not Module.valid_module(
                name=module_name,
                config=module_config,
                requires_timeout=self.global_modules_config.requires_timeout,
                requires_working_directory=self.config_directory,
            ):
                continue

            module = Module(
                name=module_name,
                module_config=module_config,
                module_directory=self.config_directory,
                replacer=self.interpolate_string,
                context_store=self.application_context,
                global_modules_config=self.global_modules_config,
                dry_run=dry_run,
            )
            self.modules[module.name] = module

        # Remove modules which depends on other missing modules
        Requirement.pop_missing_module_dependencies(self.modules)

        # Initialize the config directory watcher, but don't start it yet
        self.directory_watcher = DirectoryWatcher(
            directory=self.config_directory,
            on_modified=self.file_system_modified,
        )

        logger.info('Enabled modules: ' + ', '.join(self.modules.keys()))

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

            # Perform setup actions not yet executed
            self.setup()

            # Perform all startup actions
            self.startup()
        elif self.last_module_events != self.module_events():
            # One or more module events have changed, execute the event blocks
            # of these modules.

            for module_name, event in self.module_events().items():
                if not self.last_module_events[module_name] == event:
                    logger.info(
                        f'[module/{module_name}] New event "{event}". '
                        'Executing actions.',
                    )
                    self.execute(
                        action='all',
                        block='on_event',
                        module=self.modules[module_name],
                    )
                    self.last_module_events[module_name] = event

    def has_unfinished_tasks(self) -> bool:
        """Return True if there are any module tasks due."""
        if not self.startup_done:
            return True
        else:
            return self.last_module_events != self.module_events()

    def time_until_next_event(self) -> timedelta:
        """Time left until first event change of any of the modules managed."""
        try:
            return min(
                module.event_listener.time_until_next_event()
                for module
                in self.modules.values()
            )
        except ValueError:
            return timedelta.max

    def execute(
        self,
        action: str,
        block: str,
        module: Optional[Module] = None,
    ) -> None:
        """
        Execute action(s) specified in managed modules.

        The module actions are executed according to their specified priority.
        First import context, then symlink, and so on...

        :param action: Action to be perfomed. If given 'all', then all actions
            will be performed.
        :param block: Action block to be executed, for example 'on_exit'.
        :module: Specific module to be executed. If not provided, then all
            managed modules will be executed.
        """
        assert block in ('on_setup', 'on_startup', 'on_event', 'on_exit')

        modules: Iterable[Module]
        if isinstance(module, Module):
            modules = (module, )
        else:
            modules = self.modules.values()

        if action == 'all':
            all_actions = filter(
                lambda x: x != 'trigger',
                ActionBlock.action_types.keys(),
            )
        else:
            all_actions = (action,)  # type: ignore

        for specific_action in all_actions:
            for module in modules:
                module.execute(
                    action=specific_action,
                    block=block,
                    dry_run=self.dry_run,
                )

    def setup(self) -> None:
        """
        Run setup actions specified by the managed modules, not yet executed.
        """
        self.execute(action='all', block='on_setup')

    def startup(self):
        """
        Run all startup actions specified by the managed modules.

        Also starts the directory watcher in $ASTRALITY_CONFIG_HOME.
        """
        assert not self.startup_done
        self.execute(action='all', block='on_startup')
        self.directory_watcher.start()
        self.startup_done = True

    def exit(self):
        """
        Run all exit tasks specified by the managed modules.

        Also close all temporary file handlers created by the modules.
        """
        self.execute(action='all', block='on_exit')

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

            module.execute(
                action='all',
                block='on_modified',
                path=modified,
                dry_run=self.dry_run,
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
        config_files = (
            self.config_directory / 'astrality.yml',
            self.config_directory / 'modules.yml',
            self.config_directory / 'context.yml',
        )

        if modified in config_files:
            logger.info(
                f'$ASTRALITY_CONFIG_HOME/{modified.name} has been modified!',
            )
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
        if not self.application_config.get(
            'astrality',
            {},
        ).get(
            'hot_reload_config',
            False,
        ):
            # Hot reloading is not enabled, so we return early
            logger.info('"hot_reload" disabled.')
            return

        # Hot reloading is enabled, get the new configuration dict
        logger.info('Reloading $ASTRALITY_CONFIG_HOME...')
        (
            new_application_config,
            new_modules,
            new_context,
            directory,
        ) = user_configuration(
            config_directory=self.config_directory,
        )

        try:
            # Reinstantiate this object
            new_module_manager = ModuleManager(
                config=new_application_config,
                modules=new_modules,
                context=new_context,
                directory=directory,
            )

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
                        compile_action.execute(dry_run=self.dry_run)

                for stow_action in action_block._stow_actions:
                    if modified in stow_action:
                        stow_action.execute(dry_run=self.dry_run)

                # TODO: Test this branch
                for copy_action in action_block._copy_actions:
                    if modified in copy_action:
                        copy_action.execute(dry_run=self.dry_run)

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

    @property
    def keep_running(self) -> bool:
        """Return True if ModuleManager needs to keep running."""
        if self.reprocess_modified_files:
            return True

        if any(module.keep_running for module in self.modules.values()):
            return True

        current_process = psutil.Process()
        children = current_process.children(recursive=False)
        return bool(children)

    def __len__(self) -> int:
        """Return the number of managed modules."""
        return len(self.modules)

    def __del__(self) -> None:
        """Close filesystem watcher if enabled."""
        if hasattr(self, 'directory_watcher'):
            self.directory_watcher.stop()
