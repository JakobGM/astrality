"""
Module defining class-representation of module actions.

Each action class type encapsulates the user specified options available for
that specific action type. The action itself can be performed by invoking the
object method `execute()`.

One of the main goals with Action, is that the arity of execute is 0.
This means that we unfortunately need to pass a reference to global mutable
state, i.e. the context store.

Another goal is that none of the subclasses require the global configuration
of the entire application, just the action configuration itself. Earlier
implementations required GlobalApplicationConfig to be passed arround in the
entire run-stack, which was quite combersome. Some of the limitations with this
approach could be solved if we implement GlobalApplicationConfig as a singleton
which could be imported and accessed independently from other modules.
"""

import abc
import hashlib
import logging
import os
from collections import defaultdict
from pathlib import Path
from typing import (
    Any,
    Callable,
    DefaultDict,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    Union,
)

from mypy_extensions import TypedDict

from astrality import compiler, utils
from astrality import config
from astrality.context import Context
from astrality import persistence
from astrality.xdg import XDG

Replacer = Callable[[str], str]


class Action(abc.ABC):
    """
    Superclass for module action types.

    :param options: A dictionary containing the user options for a given module
        action type.
    :param directory: The directory used as anchor for relative paths. This
        must be an absolute path.
    :param replacer: Placeholder substitutor of string user options.
    :param context_store: A reference to the global context store.
    :param creation_store: ModuleCreatedFiles object which stores which files
        that are created by the different module actions.
    """

    directory: Path
    priority: int
    Options = Union[
        'CompileDict',
        'CopyDict',
        'ImportContextDict',
        'RunDict',
        'StowDict',
        'SymlinkDict',
        'TriggerDict',
    ]

    def __init__(
        self,
        options: 'Action.Options',
        directory: Path,
        replacer: Replacer,
        context_store: Context,
        creation_store: 'persistence.ModuleCreatedFiles',
    ) -> None:
        """Contstruct action object."""
        # If no options are provided, use null object pattern
        self.null_object = not bool(options)

        assert directory.is_absolute()
        self.directory = directory
        self.context_store = context_store
        self.creation_store = creation_store
        self._options = options
        self._replace = replacer

    def replace(self, string: str) -> str:
        """
        Return converted string, substitution defined by `replacer`.

        This is used to replace placeholders such as {event}.
        This redirection is necessary due to python/mypy/issues/2427

        :param string: String configuration option.
        :return: String with placeholders substituted.
        """
        return self._replace(string)

    def option(self, key: str, default: Any = None, path: bool = False) -> Any:
        """
        Return user specified action option.

        All option value access should go through this helper function, as
        it replaces relevant placeholders users might have specified.

        :param key: The key of the user option that should be retrieved.
        :param default: Default return value if key not found.
        :param path: If True, convert string path to Path.is_absolute().
        :return: Processed action configuration value.
        """
        option_value = self._options.get(key, default)

        if option_value is None:
            return None
        elif path:
            # The option value represents a path, that should be converted
            # to an absolute pathlib.Path object
            assert isinstance(option_value, str)
            substituted_string_path = self.replace(option_value)
            return self._absolute_path(of=substituted_string_path)
        elif isinstance(option_value, str):
            # The option is a string, and any placeholders should be
            # substituted before it is returned. We also expand any environment
            # variables that might be present.
            return os.path.expandvars(self.replace(option_value))
        else:
            return option_value

    def _absolute_path(self, of: str) -> Path:
        """
        Return absolute path from relative string path.

        :param of: Relative path.
        :return: Absolute path anchored to `self.directory`.
        """
        return config.expand_path(
            path=Path(of),
            config_directory=self.directory,
        )

    @abc.abstractmethod
    def execute(self, dry_run: bool = False) -> Any:
        """
        Execute defined action.

        :param dry_run: If external side effects should be skipped.
        """

    def __repr__(self) -> str:
        """Return string representation of Action object."""
        return self.__class__.__name__ + f'({self._options})'


class RequiredImportContextDict(TypedDict):
    """Required fields of a import_context action."""

    from_path: str


class ImportContextDict(RequiredImportContextDict, total=False):
    """Allowable fields of an import_context action."""

    from_section: str
    to_section: str


class ImportContextAction(Action):
    """
    Import context into global context store.

    :param context_store: A mutable reference to the global context store.

    See :class:`Action` for documentation for the other parameters.
    """

    priority = 100
    context_store: compiler.Context

    def execute(self, dry_run: bool = False) -> None:
        """
        Import context section(s) according to user configuration block.

        :param dry_run: This parameter is ignored, as import_context only has
            internal side effects.
        """
        if self.null_object:
            # Null object does nothing
            return None

        self.context_store.import_context(
            from_path=self.option(key='from_path', path=True),
            from_section=self.option(key='from_section'),
            to_section=self.option(key='to_section'),
        )


class RequiredCompileDict(TypedDict):
    """Required fields of compile action."""

    content: str


class CompileDict(RequiredCompileDict, total=False):
    """Allowable fields of compile action."""

    target: str
    include: str
    permissions: str


class CompileAction(Action):
    """Compile template action."""

    _options: CompileDict

    priority = 400

    def __init__(self, *args, **kwargs) -> None:
        """Construct compile action object."""
        super().__init__(*args, **kwargs)
        self._performed_compilations: DefaultDict[Path, Set[Path]] = \
            defaultdict(set)

    def execute(self, dry_run: bool = False) -> Dict[Path, Path]:
        """
        Compile template source to target destination.

        :param dry_run: If True, skip and log compilation(s).
        :return: Dictionary with template content keys and target path values.
        """
        if self.null_object:
            # Null objects do nothing
            return {}
        elif 'target' not in self._options:
            # If no target is specified, we create a deterministic target.
            template = self.option(key='content', path=True)
            target = self.create_compilation_target(template=template)
            self._options['target'] = str(target)

        # These might either be file paths or directory paths
        template_source = self.option(key='content', path=True)
        target_source = self.option(key='target', path=True)
        if not template_source.exists():
            logger = logging.getLogger(__name__)
            logger.error(
                f'Could not compile template "{template_source}" '
                f'to target "{target_source}". No such path!',
            )
            return {}

        compile_pairs = utils.resolve_targets(
            content=template_source,
            target=target_source,
            include=self.option(key='include', default=r'(.+)'),
        )
        permissions = self.option(key='permissions')

        for content_file, target_file in compile_pairs.items():
            if dry_run:
                logger = logging.getLogger(__name__)
                logger.info(
                    f'SKIPPED: '
                    f'[Compiling] Template: "{content_file}" '
                    f'-> Target: "{target_file}"',
                )
            else:
                self.creation_store.backup(path=target_file)
                compiler.compile_template(
                    template=content_file,
                    target=target_file,
                    context=self.context_store,
                    shell_command_working_directory=self.directory,
                    permissions=permissions,
                )
                self.creation_store.insert_creation(
                    content=content_file,
                    target=target_file,
                    method=persistence.CreationMethod.COMPILE,
                )

            self._performed_compilations[content_file].add(target_file)

        return compile_pairs

    def performed_compilations(self) -> DefaultDict[Path, Set[Path]]:
        """
        Return dictionary containing all performed compilations.

        :return: Dictinary with keys containing compiled templates, and values
            as a set of target paths.
        """
        return self._performed_compilations.copy()

    def create_compilation_target(self, template: Path) -> Path:
        """
        Create compilation target for template with unspecified target.

        Compilation targets are stored in $XDG_DATA_HOME/astrality/compilations.
        For details regarding the implementation see:
            https://www.peterbe.com/plog/best-hashing-function-in-python

        :param name: Path to template to be compiled.
        :return: Path to deterministicly determined compilation target.
        """
        # First dump the action configuration to YAML formatted string
        yaml_config = utils.yaml_str(self._options)

        # Now encode the string into raw bytes
        yaml_config_bytes = yaml_config.encode('utf-8', errors='ignore')

        # Create a MD5 hash from the string, only using the first seven chars
        yaml_config_md5 = hashlib.md5(yaml_config_bytes).hexdigest()[:7]

        # Prepend the template name for readability
        unique_name = template.name + '-' + yaml_config_md5

        # Create compilation target in XDG data directory
        compile_target = XDG().data(resource='compilations/' + unique_name)
        return compile_target

    def __contains__(self, other) -> bool:
        """Return True if run action is responsible for template."""
        assert other.is_absolute()

        if not self.option(key='content', path=True) == other:
            # This is not a managed template, so we will not recompile
            return False

        # Return True if the template has been compiled
        return other in self.performed_compilations()


class RequiredSymlinkDict(TypedDict):
    """Required fields of symlink action user config."""

    content: str
    target: str


class SymlinkDict(RequiredSymlinkDict, total=False):
    """Allowable fields of symlink action user config."""

    include: str


class SymlinkAction(Action):
    """Symlink files Action sub-class."""

    priority = 200

    _options: SymlinkDict

    def __init__(self, *args, **kwargs) -> None:
        """Construct symlink action object."""
        super().__init__(*args, **kwargs)
        self.symlinked_files: DefaultDict[Path, Set[Path]] = \
            defaultdict(set)

    def execute(self, dry_run: bool = False) -> Dict[Path, Path]:
        """
        Symlink to `content` path from `target` path.

        :param dry_run: If True, skip and log symlink creation(s).
        :return: Dictionary with content keys and symlink values.
        """
        if self.null_object:
            return {}

        content = self.option(key='content', path=True)
        target = self.option(key='target', path=True)
        include = self.option(key='include', default=r'(.+)')
        links = utils.resolve_targets(
            content=content,
            target=target,
            include=include,
        )

        logger = logging.getLogger(__name__)
        for content, symlink in links.items():
            self.symlinked_files[content].add(symlink)
            log_msg = f'[symlink] Content "{content}" -> Target: "{symlink}".'

            if symlink.resolve() == content:
                continue

            if dry_run:
                logger.info('SKIPPED: ' + log_msg)
                continue

            logger.info(log_msg)
            symlink.parent.mkdir(parents=True, exist_ok=True)

            self.creation_store.backup(path=symlink)
            symlink.symlink_to(content)
            self.creation_store.insert_creation(
                content=content,
                target=symlink,
                method=persistence.CreationMethod.SYMLINK,
            )

        return links


class RequiredCopyDict(TypedDict):
    """Required fields of copy action user config."""

    content: str
    target: str


class CopyDict(RequiredCopyDict, total=False):
    """Allowable fields of copy action user config."""

    include: str
    permissions: str


class CopyAction(Action):
    """Copy files Action sub-class."""

    priority = 300

    _options: CopyDict

    def __init__(self, *args, **kwargs) -> None:
        """Construct copy action object."""
        super().__init__(*args, **kwargs)
        self.copied_files: DefaultDict[Path, Set[Path]] = \
            defaultdict(set)

    def execute(self, dry_run: bool = False) -> Dict[Path, Path]:
        """
        Copy from `content` path to `target` path.

        :param dry_run: If True, skip and log copy creation(s).
        :return: Dictionary with content keys and copy values.
        """
        if self.null_object:
            return {}

        content = self.option(key='content', path=True)
        target = self.option(key='target', path=True)
        include = self.option(key='include', default=r'(.+)')
        permissions = self.option(key='permissions', default=None)

        copies = utils.resolve_targets(
            content=content,
            target=target,
            include=include,
        )
        logger = logging.getLogger(__name__)
        for content, copy in copies.items():
            self.copied_files[content].add(copy)

            log_msg = f'[copy] Content: "{content}" -> Target: "{target}".'
            if dry_run:
                logger.info('SKIPPED: ' + log_msg)
                continue

            logger.info(log_msg)
            copy.parent.mkdir(parents=True, exist_ok=True)

            self.creation_store.backup(path=copy)
            utils.copy(
                source=content,
                destination=copy,
                follow_symlinks=False,
            )
            self.creation_store.insert_creation(
                content=content,
                target=copy,
                method=persistence.CreationMethod.COPY,
            )

        if permissions and not dry_run:
            for copy in copies.values():
                result = utils.run_shell(
                    command=f'chmod {permissions} "{copy}"',
                    timeout=1,
                    fallback=False,
                )

                if result is False:
                    logger = logging.getLogger(__name__)
                    logger.error(
                        f'Could not set "{permissions}" '
                        f'permissions for copy "{target}"',
                    )

        return copies

    def __contains__(self, other) -> bool:
        """Return True if path has been copied *from*."""
        return other in self.copied_files


class RequiredStowDict(TypedDict):
    """Required dictionary keys for user stow action config."""

    content: str
    target: str


class StowDict(RequiredStowDict, total=False):
    """Allowable dictionary keys for user stow action config."""

    templates: str
    non_templates: str
    permissions: str


class StowAction(Action):
    """Stow directory action."""

    non_templates_action: Union[CopyAction, SymlinkAction]
    _options: StowDict

    priority = 500

    def __init__(self, *args, **kwargs) -> None:
        """Construct stow action object."""
        super().__init__(*args, **kwargs)
        if self.null_object:
            return

        # Create equivalent compile action based on stow config
        compile_options: CompileDict = {
            'content': self._options['content'],
            'target': self._options['target'],
            'include': self._options.get('templates', r'template\.(.+)'),
        }
        if 'permissions' in self._options:
            compile_options['permissions'] = self._options['permissions']

        self.compile_action = CompileAction(
            options=compile_options,
            directory=self.directory,
            replacer=self.replace,
            context_store=self.context_store,
            creation_store=self.creation_store,
        )

        # Determine what to do with non-templates
        non_templates_action = self._options.get('non_templates', 'symlink')
        self.ignore_non_templates = non_templates_action.lower() == 'ignore'

        if non_templates_action.lower() not in ('copy', 'symlink', 'ignore'):
            logger = logging.getLogger(__name__)
            logger.error(
                f'Invalid stow non_templates parameter:'
                f'"{non_templates_action}". '
                'Should be one of "symlink", "copy", or "ignore"!',
            )
            self.ignore_non_templates = True
            return

        # Negate the `templates` regex pattern in order to match non-templates
        if 'templates' in self._options:
            excluded = r'(?!' + self._options['templates'] + r').+'
        else:
            excluded = r'(?!template\..+).+'

        # Create configuration used for either symlink or copy
        non_templates_options: Dict = {
            'content': self._options['content'],
            'target': self._options['target'],
            'include': excluded,
            'permissions': self._options.get('permissions'),
        }

        # Create action object based on parameter `non_templates`
        NonTemplatesAction: Union[Type[CopyAction], Type[SymlinkAction]]
        if non_templates_action.lower() == 'copy':
            NonTemplatesAction = CopyAction
        else:
            NonTemplatesAction = SymlinkAction

        self.non_templates_action = NonTemplatesAction(
            options=non_templates_options,
            directory=self.directory,
            replacer=self.replace,
            context_store=self.context_store,
            creation_store=self.creation_store,
        )

    def execute(self, dry_run: bool = False) -> Dict[Path, Path]:
        """
        Stow directory source to target destination.

        :param dry_run: If True, skip and log copies, symlinks, and
            compilations.
        :return: Dictionary with source keys and target values.
            Contains compiled, symlinked, and copied files.
        """
        if self.null_object:
            return {}

        if self.ignore_non_templates:
            return self.compile_action.execute(dry_run=dry_run)
        else:
            copies_or_links = self.non_templates_action.execute(dry_run=dry_run)
            compilations = self.compile_action.execute(dry_run=dry_run)
            compilations.update(copies_or_links)
            return compilations

    def managed_files(self) -> Dict[Path, Set[Path]]:
        """
        Return dictionary containing content keys and target values.

        :return: Dictinary with keys containing compiled templates, and values
            as a set of target paths. If `non_templates` is 'copy', then these
            will be included as well.
        """
        if self.null_object:
            return {}

        managed_files = self.compile_action._performed_compilations.copy()

        if isinstance(self.non_templates_action, CopyAction):
            managed_files.update(self.non_templates_action.copied_files)

        return managed_files

    def __contains__(self, other) -> bool:
        """
        Return True if stow action is responsible for file path.

        A stow action is considered to be responsible for a file path if that
        path is modified results in its tasks to be outdated, and it needs to be
        re-executed.

        :param other: File path.
        :return: Boolean indicating if path has been copied or compiled.
        """
        assert other.is_absolute()
        return other in self.managed_files()


class RunDict(TypedDict):
    """Required fields of run action user config."""

    shell: str
    timeout: Union[int, float]


class RunAction(Action):
    """Run shell command Action sub-class."""

    _options: RunDict

    priority = 600

    def execute(  # type: ignore
        self,
        default_timeout: Union[int, float] = 0,
        dry_run: bool = False,
    ) -> Optional[Tuple[str, str]]:
        """
        Execute shell command action.

        :param default_timeout: Run timeout in seconds if no specific value is
            specified in `options`.
        :param dry_run: If True, skip and log commands to be executed.
        :return: 2-tuple containing the executed command and its resulting
            stdout.
        """
        if self.null_object:
            # Null objects do nothing
            return None

        command = self.option(key='shell')
        timeout = self.option(key='timeout')

        logger = logging.getLogger(__name__)
        if dry_run:
            logger.info(
                f'SKIPPED: [run] Command: "{command}" (timeout={timeout}).',
            )
            return command, ''

        logger.info(f'Running command "{command}".')
        result = utils.run_shell(
            command=command,
            timeout=timeout or default_timeout,
            working_directory=self.directory,
        )
        return command, result


class TriggerDictRequired(TypedDict):
    """Required fields of a trigger module action."""

    block: str


class TriggerDict(TriggerDictRequired, total=False):
    """Optional fields of a trigger module action."""

    path: str


class Trigger:
    """
    A class representing an instruction to trigger a specific action block.

    :ivar block: The block to be trigger, for example 'on_startup',
        'on_event', 'on_exit', or 'on_modified'.
    :ivar specified_path: The string path specified for a 'on_modified' block.
    :ivar relative_path: The relative pathlib.Path specified by
        `specified_path`.
    :ivar absolute_path: The absolute path specified by `specified_path`.
    """

    block: str
    specified_path: Optional[str]
    relative_path: Optional[Path]
    absolute_path: Optional[Path]

    def __init__(
        self,
        block: str,
        specified_path: Optional[str] = None,
        relative_path: Optional[Path] = None,
        absolute_path: Optional[Path] = None,
    ) -> None:
        """Construct trigger instruction."""
        self.block = block
        self.specified_path = specified_path
        self.relative_path = relative_path
        self.absolute_path = absolute_path


class TriggerAction(Action):
    """Action sub-class representing a trigger action."""

    _options: TriggerDict

    priority = 0

    def execute(self, dry_run: bool = False) -> Optional[Trigger]:
        """
        Return trigger instruction.

        If no trigger is specified, return None.

        :param dry_run: This parameter is ignored.
        :return: Optional :class:`.Trigger` instance.
        """
        if self.null_object:
            """Null objects do nothing."""
            return None

        block = self.option(key='block')

        if block != 'on_modified':
            # We do not need any paths, as the trigger block is not relative to
            # any modified path.
            return Trigger(block=block)

        # The modified path specified by the user configuration
        specified_path = self.option(key='path')

        # Instantiate relative and absolute pathlib.Path objects
        relative_path = Path(specified_path)
        absolute_path = self._absolute_path(of=specified_path)

        # Return 'on_modified' Trigger object with path information
        return Trigger(
            block=block,
            specified_path=specified_path,
            relative_path=relative_path,
            absolute_path=absolute_path,
        )


class ActionBlockDict(TypedDict, total=False):
    """Valid keys in an action block."""

    import_context: Union[ImportContextDict, List[ImportContextDict]]
    compile: Union[CompileDict, List[CompileDict]]
    run: Union[RunDict, List[RunDict]]
    trigger: Union[TriggerDict, List[TriggerDict]]


class ActionBlock:
    """
    Class representing a module action block, e.g. 'on_startup'.

    :param action_block: Dictionary containing all actions to be performed.
    :param directory: The directory used as anchor for relative paths. This
        must be an absolute path.
    :param replacer: Placeholder substitutor of string user options.
    :param context_store: A reference to the global context store.
    :param module_name: Name of module owning ActionBlock.
    :param global_modules_config: Global configuration object.
    """

    _compile_actions: List[CompileAction]
    _copy_actions: List[CopyAction]
    _import_context_actions: List[ImportContextAction]
    _run_actions: List[RunAction]
    _stow_actions: List[StowAction]
    _symlink_actions: List[SymlinkAction]
    _trigger_actions: List[TriggerAction]

    action_types = {
        'import_context': ImportContextAction,
        'symlink': SymlinkAction,
        'copy': CopyAction,
        'compile': CompileAction,
        'stow': StowAction,
        'run': RunAction,
        'trigger': TriggerAction,
    }

    def __init__(
        self,
        action_block: ActionBlockDict,
        directory: Path,
        replacer: Replacer,
        context_store: compiler.Context,
        global_modules_config: 'config.GlobalModulesConfig',
        module_name: str,
    ) -> None:
        """Construct ActionBlock object."""
        assert directory.is_absolute()
        if not global_modules_config:
            # TODO: This is only the case in testing, and should be explicitly
            # provided in all tests at some point.
            global_modules_config = config.GlobalModulesConfig(
                config={},
                config_directory=directory,
            )
        self.action_block = action_block
        self.module_name = module_name
        self.run_timeout = global_modules_config.run_timeout

        creation_store = global_modules_config.created_files.wrapper_for(
            module=self.module_name,
        )
        for identifier, action_type in self.action_types.items():
            # Create and persist a list of all ImportContextAction objects
            setattr(
                self,
                f'_{identifier}_actions',
                [
                    action_type(
                        options=action_options,
                        directory=directory,
                        replacer=replacer,
                        context_store=context_store,
                        creation_store=creation_store,
                    )
                    for action_options
                    in self.action_options(identifier=identifier)
                ],
            )

    def action_options(self, identifier: str) -> List[Action.Options]:
        """
        Return all action configs of type 'identifier'.

        :param identifier: Action type, such as 'run' or 'compile'.
        :return: List of action options of that type.
        """
        return utils.cast_to_list(                  # type: ignore
            self.action_block.get(identifier, {}),  # type: ignore
        )

    def import_context(self, dry_run: bool = False) -> None:
        """Import context into global context store."""
        for import_context_action in self._import_context_actions:
            import_context_action.execute(dry_run=dry_run)

    def symlink(self, dry_run: bool = False) -> None:
        """Symlink files."""
        for symlink_action in self._symlink_actions:
            symlink_action.execute(dry_run=dry_run)

    def copy(self, dry_run: bool = False) -> None:
        """Copy files."""
        for copy_action in self._copy_actions:
            copy_action.execute(dry_run=dry_run)

    def compile(self, dry_run: bool = False) -> None:
        """Compile templates."""
        for compile_action in self._compile_actions:
            compile_action.execute(dry_run=dry_run)

    def stow(self, dry_run: bool = False) -> None:
        """Stow directory contents."""
        for stow_action in self._stow_actions:
            stow_action.execute(dry_run=dry_run)

    def run(
        self,
        default_timeout: Optional[Union[int, float]] = None,
        dry_run: bool = False,
    ) -> Tuple[Tuple[str, str], ...]:
        """
        Run shell commands.

        :param default_timeout: How long to wait for run commands to exit
        :return: Tuple of 2-tuples containing (shell_command, stdout,)
        """
        results: Tuple[Tuple[str, str], ...] = tuple()
        for run_action in self._run_actions:
            result = run_action.execute(
                default_timeout=default_timeout or self.run_timeout,
                dry_run=dry_run,
            )
            if result:
                # Run action is not null object, so we can return results
                command, stdout = result
                results += ((command, stdout),)

        return results

    def triggers(self, dry_run: bool = False) -> Tuple[Trigger, ...]:
        """
        Return all trigger instructions specified in action block.

        :return: Tuple of Trigger objects specified in action block.
        """
        return tuple(
            trigger_action.execute(dry_run=dry_run)  # type: ignore
            for trigger_action
            in self._trigger_actions
            if not trigger_action.null_object
        )

    def execute(
        self,
        default_timeout: Union[int, float],
        dry_run: bool = False,
    ) -> None:
        """
        Execute all actions in action block.

        The order of execution is:
            1) Perform all context imports into the context store.
            2) Compile all templates.
            3) Run all shell commands.
        """
        self.import_context()
        self.compile()
        self.run(default_timeout=default_timeout, dry_run=dry_run)

    def performed_compilations(self) -> DefaultDict[Path, Set[Path]]:
        """
        Return all earlier performed compilations.

        :return: Dictionary with template keys and target path set.
        """
        all_compilations: DefaultDict[Path, Set[Path]] = defaultdict(set)
        for compile_action in self._compile_actions:
            compilations = compile_action.performed_compilations()
            for template, targets in compilations.items():
                all_compilations[template] |= targets

        return all_compilations


class SetupActionBlock(ActionBlock):
    """Setup action block which only executes actions once."""

    def action_options(self, identifier: str) -> List[Action.Options]:
        """
        Return action configs of 'identifier' type that have not been executed.

        :param identifier: Action type, such as 'run' or 'compile'.
        :return: List of action options of that type.
        """
        action_options = super().action_options(identifier)

        if not hasattr(self, 'executed_setup_actions'):
            self.executed_setup_actions = persistence.ExecutedActions(
                module_name=self.module_name,
            )

        not_executed = [
            action_option
            for action_option
            in action_options
            if self.executed_setup_actions.is_new(
                action_type=identifier,
                action_options=action_option,
            )
        ]
        self.executed_setup_actions.write()
        return not_executed
