"""Module implementing user configured custom functionality."""

from collections import namedtuple
from datetime import timedelta
import logging
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union

from jinja2.exceptions import TemplateNotFound

from astrality import compiler
from astrality.compiler import context
from astrality.config import (
    ApplicationConfig,
    GlobalModulesConfig,
    expand_path,
    insert_into,
    user_configuration,
)
from astrality.event_listener import EventListener, event_listener_factory
from astrality.filewatcher import DirectoryWatcher
from astrality.resolver import Resolver
from astrality.utils import run_shell


ModuleConfig = Dict[str, Any]

ContextSectionImport = namedtuple(
    'ContextSectionImport',
    ['into_section', 'from_section', 'from_config_file'],
)
Template = namedtuple(
    'Template',
    ['source', 'target'],
)
WatchedFile = namedtuple(
    'WatchedFile',
    ['path', 'module', 'specified_path'],
)

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
    """

    def __init__(
        self,
        module_config: ModuleConfig,
        module_directory: Path,
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

        section = next(iter(module_config.keys()))
        self.name: str = section[7:]

        # The source directory for the module, determining how to interpret
        # relative paths in the module config
        self.directory = module_directory

        self.module_config = module_config[section]
        self.populate_event_blocks()

        # Import trigger actions into their respective event blocks
        self.import_trigger_actions()

        # Use static event_listener if no event_listener is specified
        self.event_listener: EventListener = event_listener_factory(
            self.module_config.get('event_listener', {'type': 'static'}),
        )

    def populate_event_blocks(self) -> None:
        """
        Populate non-configured actions within event blocks.

        This prevents us from having to use .get() all over the Module.
        """
        for event_block in ('on_startup', 'on_event', 'on_exit', ):
            configured_event_block = self.module_config.get(event_block, {})
            self.module_config[event_block] = {
                'import_context': [],
                'compile': [],
                'run': [],
                'trigger': [],
            }
            self.module_config[event_block].update(configured_event_block)

        if not 'on_modified' in self.module_config:
            self.module_config['on_modified'] = {}
        else:
            for template_name in self.module_config['on_modified'].keys():
                configured_event_block = self.module_config['on_modified'][template_name]
                self.module_config['on_modified'][template_name] = {
                    'import_context': [],
                    'compile': [],
                    'run': [],
                    'trigger': [],
                }
                self.module_config['on_modified'][template_name].update(configured_event_block)

        # Convert any single actions into a list of that action, allowing
        # users to not use lists in their configuration if they only have one
        # action
        for event_block in (
            self.module_config['on_startup'],
            self.module_config['on_event'],
            self.module_config['on_exit'],
            *self.module_config['on_modified'].values(),
        ):
            for action in ('import_context', 'compile', 'run', 'trigger',):
                if not isinstance(event_block[action], list):  # type: ignore
                    event_block[action] = [event_block[action]]  # type: ignore

    def import_trigger_actions(self) -> None:
        """If an event block defines trigger events, import those actions."""
        event_blocks = (
            self.module_config['on_startup'],
            self.module_config['on_event'],
            self.module_config['on_exit'],
            *self.module_config['on_modified'].values(),
        )
        for event_block in event_blocks:
            event_blocks_to_import = event_block['trigger']

            for event_block_to_import in event_blocks_to_import:
                self._import_event_block(
                    from_event_block=event_block_to_import,
                    into=event_block,
                )

    def _import_event_block(
        self,
        from_event_block: str,
        into: Dict[str, Any],
    ) -> None:
        """Merge one event block with another one."""
        if 'on_modified:' in from_event_block:
            template = from_event_block[12:]
            from_event_block_dict = self.module_config['on_modified'].get(template, {})
        else:
            from_event_block_dict = self.module_config[from_event_block]

        into['run'].extend(from_event_block_dict['run'])
        into['import_context'].extend(from_event_block_dict['import_context'])
        into['compile'].extend(from_event_block_dict['compile'])

    def commands(
        self,
        block: str,
        modified_file: Optional[str] = None,
    ) -> Tuple[str, ...]:
        """
        Return all shell commands to be run for a specific block, i.e.
        any of on_startup, on_event, on_exit, or on_modified.

        A modified file action block is given by block='on_modified:file/path'.
        """

        startup_commands: List[str]

        if modified_file:
            assert block == 'on_modified'
            startup_commands = self.module_config['on_modified'][modified_file]['run']
        else:
            assert block in ('on_startup', 'on_event', 'on_exit',)
            startup_commands = self.module_config[block]['run']

        if len(startup_commands) == 0:
            logger.debug(f'[module/{self.name}] No {block} command specified.')
            return ()
        else:
            return tuple(
                self.interpolate_string(command)
                for command
                in startup_commands
            )

    def startup_commands(self) -> Tuple[str, ...]:
        """Return commands to be run on Module instance startup."""
        return self.commands('on_startup')

    def on_event_commands(self) -> Tuple[str, ...]:
        """Commands to be run when self.event_listener event changes."""
        return self.commands('on_event')

    def exit_commands(self) -> Tuple[str, ...]:
        """Commands to be run on Module instance shutdown."""
        return self.commands('on_exit')

    def modified_commands(self, specified_path: str) -> Tuple[str, ...]:
        """Commands to be run when a module template is modified."""
        return self.commands('on_modified', specified_path)

    def context_section_imports(
        self,
        trigger: str,
        modified: Optional[str] = None,
    ) -> Tuple[ContextSectionImport, ...]:
        """
        Return what to import into the global application_context.

        Trigger is one of 'on_startup', 'on_event', 'on_modified, or 'on_exit'.
        This determines which section of the module is used to get the context
        import specification from.

        If trigger is 'on_modified', you also need to specify which file is
        modified, in order to get the correct section.
        """
        import_config: List[Dict[str, str]]
        if modified:
            assert trigger == 'on_modified'
            import_config = self.module_config[trigger][modified]['import_context']
        else:
            assert trigger in ('on_startup', 'on_event', 'on_exit',)
            import_config = self.module_config[trigger]['import_context']

        context_section_imports = []
        for context_import in import_config:
            # Insert placeholders
            from_path = self.interpolate_string(context_import['from_path'])

            from_section: Optional[str]
            to_section: Optional[str]

            if 'from_section' in context_import:
                from_section = self.interpolate_string(context_import['from_section'])

                # If no `to_section` is specified, use the same section as
                # `from_section`
                to_section = self.interpolate_string(
                    context_import.get('to_section', from_section),
                )
            else:
                # From section is not specified, so set both to None, indicating
                # a wish to import *all* sections
                from_section = None
                to_section = None

            # Get the relative path to file containing the context
            config_path = Path(from_path)

            # Isert a ContextSectionImport tuple into the return value
            context_section_imports.append(
                ContextSectionImport(
                    into_section=to_section,
                    from_section=from_section,
                    from_config_file=config_path,
                )
            )

        return tuple(context_section_imports)


    def interpolate_string(self, string: str) -> str:
        """
        Replace all module placeholders in string.

        For now, the module only replaces {event} placeholders.
        """
        return string.replace('{event}', self.event_listener.event())

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
            valid_module_name = module_name.split('/')[0].lower() == 'module'  # type: ignore
            enabled = section[module_name].get('enabled', True)
            if not (valid_module_name and enabled):
                return False

        except KeyError:
            return False

        # The module is enabled, now check if all requirements are satisfied
        requires = section[module_name].get('requires')
        if not requires:
            return True
        else:
            if isinstance(requires, str):
                requires = [requires]

            for requirement in requires:
                if run_shell(command=requirement, fallback=False) is False:
                    logger.warning(
                        f'[{module_name}] Module does not satisfy requirement "{requirement}".',
                    )
                    return False

            logger.info(
                f'[{module_name}] Module satisfies all requirements.'
            )
            return True

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
        self.recompile_modified_templates = self.global_modules_config.recompile_modified_templates

        self.modules: Dict[str, Module] = {}

        # Application context is used in compiling external config sources
        application_context = context(config)

        # Insert externally managed modules
        for external_module_source in self.global_modules_config.external_module_sources:
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
                    requires_timeout=self.global_modules_config.requires_timeout,
                    requires_working_directory=module_directory,
                ) or section not in self.global_modules_config.enabled_modules:
                    continue

                module = Module(
                    module_config=module_config,
                    module_directory=module_directory,
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
            )
            self.modules[module.name] = module

        self.templates = self.prepare_templates(self.modules.values())
        self.string_replacements = self.generate_string_replacements(self.templates)
        self.on_modified_paths = self.find_on_modified_paths(self.modules.values())

        # Initialize the config directory watcher, but don't start it yet
        self.directory_watcher = DirectoryWatcher(
            directory=self.config_directory,
            on_modified=self.file_system_modified,
        )

        logger.info('Enabled modules: ' + ', '.join(self.modules.keys()))

    def __len__(self) -> int:
        """Return the number of managed modules."""
        return len(self.modules)

    def prepare_templates(
        self,
        modules: Iterable[Module],
    ) -> Dict[str, Template]:
        """
        Prepare the use of templates that could be compiled by `modules`.

        Returns a dictionary where the user provided path to the template is
        the key, and the value is a Template NamedTuple instance, containing
        the source and target Paths of the template.
        """
        templates: Dict[str, Template] = {}

        for module in modules:
            # All the module blocks which can contain compile actions
            for block in (
                    module.module_config['on_startup'],
                    module.module_config['on_event'],
                    module.module_config['on_exit'],
                    *module.module_config['on_modified'].values(),
            ):
                for compile_action in block['compile']:
                    specified_source = compile_action['template']
                    absolute_source = expand_path(
                        path=Path(specified_source),
                        config_directory=module.directory,
                    )

                    if 'target' in compile_action:
                        target = expand_path(
                            path=Path(compile_action['target']),
                            config_directory=module.directory,
                        )
                    else:
                        target = self.create_temp_file(name=module.name)

                    templates[specified_source] = Template(
                        source=absolute_source,
                        target=target,
                    )

        return templates


    def find_on_modified_paths(
        self,
        modules: Iterable[Module],
    ) -> Dict[Path, WatchedFile]:
        """
        Return a dictionary keyed to all modification watched file paths.

        Return a dictionary with the paths to watched files as the keys and
        WatchedFile instances as values.
        """
        on_modified_paths: Dict[Path, WatchedFile] = {}

        for module in modules:
            for watched_for_modification in module.module_config['on_modified'].keys():
                on_modified_path = expand_path(
                    path=Path(watched_for_modification),
                    config_directory=module.directory,
                )
                on_modified_paths[on_modified_path] = WatchedFile(
                    path=on_modified_path,
                    module=module,
                    specified_path=watched_for_modification,
                )

        return on_modified_paths

    def generate_string_replacements(
        self,
        templates: Dict[str, Template],
    ) -> Dict[str, str]:
        """
        Returns a dictionary containing all string replacements keyed to their
        placeholders.

        Includes template path placeholders replaced with the compilation
        target path.
        """
        string_replacements: Dict[str, str] = {}

        for specified_path, template in templates.items():
            string_replacements[specified_path] = str(template.target)

        return string_replacements

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
            self.import_context_sections('on_startup')
            self.compile_templates('on_startup')
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
            context_section_imports = module.context_section_imports(trigger)

            for csi in context_section_imports:
                self.application_context = insert_into(
                    context=self.application_context,
                    section=csi.into_section,
                    from_section=csi.from_section,
                    from_config_file=expand_path(
                        path=csi.from_config_file,
                        config_directory=module.directory,
                    ),
                )

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


        for module in self.modules.values():
            for compilation in module.module_config[trigger]['compile']:
                specified_path = compilation['template']
                template = self.templates[specified_path]
                self.compile_template(
                    source=template.source,
                    target=template.target,
                )


    def compile_template(self, source: Path, target: Path) -> None:
        """
        Compile a single template given by its shortname.

        A shortname is given either by shortname, implying that the module given
        defines that template, or by module_name.shortname, making it explicit.
        """
        try:
            compiler.compile_template(
                template=source,
                target=target,
                context=self.application_context,
                shell_command_working_directory=self.config_directory,
            )
        except TemplateNotFound:
            logger.error(
                f'Could not compile template "{source}" to target "{target}". '
                'Template does not exist.'
            )

    def startup(self):
        """Run all startup commands specified by the managed modules."""
        for module in self.modules.values():
            startup_commands = module.startup_commands()
            for command in startup_commands:
                logger.info(f'[module/{module.name}] Running startup command.')
                self.run_shell(
                    command=command,
                    timeout=self.global_modules_config.run_timeout,
                    working_directory=module.directory,
                    module_name=module.name,
                )

        self.startup_done = True

        # Start watching config directory for file changes
        self.directory_watcher.start()

    def run_on_event_commands(
        self,
        module: Module,
    ):
        """Run all event change commands specified by a managed module."""
        on_event_commands = module.on_event_commands()
        for command in on_event_commands:
            logger.info(f'[module/{module.name}] Running event command.')
            self.run_shell(
                command=command,
                timeout=self.global_modules_config.run_timeout,
                working_directory=module.directory,
                module_name=module.name,
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
            exit_commands = module.exit_commands()
            for command in exit_commands:
                logger.info(f'[module/{module.name}] Running exit command.')
                self.run_shell(
                    command=command,
                    timeout=self.global_modules_config.run_timeout,
                    working_directory=module.directory,
                    module_name=module.name,
                )

        if hasattr(self, 'temp_files'):
            for temp_file in self.temp_files:
                temp_file.close()

            # Prevent files from being closed again
            del self.temp_files

        # Stop watching config directory for file changes
        self.directory_watcher.stop()

    def on_modified(self, modified: Path) -> None:
        """
        Perform actions when a watched file is modified.
        """
        watched_file = self.on_modified_paths[modified]
        module = watched_file.module
        specified_path = watched_file.specified_path

        # First import context sections in on_modified block
        for csi in module.context_section_imports(
            trigger='on_modified',
            modified=specified_path,
        ):
            self.application_context = insert_into(
                context=self.application_context,
                section=csi.into_section,
                from_section=csi.from_section,
                from_config_file=expand_path(
                    path=csi.from_config_file,
                    config_directory=module.directory,
                ),
            )

        # Now compile templates specified in on_modified block
        for compilation in module.module_config['on_modified'][specified_path]['compile']:
            template = self.templates[compilation['template']]
            self.compile_template(
                source=template.source,
                target=template.target,
            )


        # Lastly, run commands specified in on_modified block
        modified_commands = module.modified_commands(specified_path)
        for command in modified_commands:
            logger.info(f'[module/{module.name}] Running modified command.')
            self.run_shell(
                command=command,
                timeout=self.global_modules_config.run_timeout,
                working_directory=module.directory,
                module_name=module.name,
            )


    def file_system_modified(self, modified: Path) -> None:
        """
        Callback for when files within the config directory are modified.

        Run any context imports, compilations, and shell commands specified
        within the on_modified event block of each module.

        Also, if hot_reload is True, we reinstantiate the ModuleManager object
        if the application configuration has been modified.
        """
        if modified == self.application_config['_runtime']['config_directory'] / 'astrality.yml':
            self.on_application_config_modified()
        elif modified in self.on_modified_paths:
            # The modified file is specified in one of the modules
            self.on_modified(modified)
        else:
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
        except:
            # New configuration is invalid, just keep the old one
            # TODO: Test this behaviour
            logger.error('New configuration detected, but it is invalid!')
            pass


    def recompile_modified_template(self, modified: Path):
        """
        Recompile any modified template if configured.

        This requires setting the global setting:
        recompile_modified_templates: true
        """
        if not self.recompile_modified_templates:
            return

        for template in self.templates.values():
            if template.source == modified:
                self.compile_template(
                    source=template.source,
                    target=template.target,
                )

    def run_shell(
        self,
        command: str,
        timeout: Union[int, float],
        working_directory: Path,
        module_name: Optional[str] = None,
    ) -> None:
        """Run a shell command defined by a managed module."""

        command = self.interpolate_string(command)

        if module_name:
            logger.info(f'[module/{module_name}] Running command "{command}".')

        run_shell(
            command=command,
            timeout=timeout,
            working_directory=working_directory,
        )

    def interpolate_string(self, string: str) -> str:
        """Replace all template placeholders with the compilation path."""

        for specified_path, template in self.templates.items():
            string = string.replace(
                '{' + specified_path + '}',
                str(template.target),
            )
        return string

    def create_temp_file(self, name) -> Path:
        """Create a temp file used as a compilation target, returning its path."""

        temp_file = NamedTemporaryFile(  # type: ignore
            prefix=name + '-',
            # dir=Path(self.temp_directory),
        )

        # NB: These temporary files need to be persisted during the entirity of
        # the scripts runtime, since the files are deleted when they go out of
        # scope.
        if not hasattr(self, 'temp_files'):
            self.temp_files = [temp_file]
        else:
            self.temp_files.append(temp_file)

        return Path(temp_file.name)
