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
import logging
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import (
    Any,
    Callable,
    List,
    Optional,
    Tuple,
    Union,
)

from jinja2.exceptions import TemplateNotFound
from mypy_extensions import TypedDict

from astrality import compiler, utils
from astrality.config import expand_path, insert_into

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
    """

    directory: Path
    priority: int

    def __init__(
        self,
        options: Union['ImportContextDict', 'CompileDict', 'RunDict'],
        directory: Path,
        replacer: Replacer,
        context_store: compiler.Context,
    ) -> None:
        """Contstruct action object."""
        # If no options are provided, use null object pattern
        self.null_object = not bool(options)

        assert directory.is_absolute()
        self.directory = directory
        self._options = options
        self._replace = replacer
        self.context_store = context_store

    def replace(self, string: str) -> str:
        """
        Return converted string, substitution defined by `replacer`.

        This is used to replace placeholders such as {event}.
        This redirection is necessary due to python/mypy/issues/2427

        :param string: String configuration option.
        :return: String with placeholders substituted.
        """
        return self._replace(string)

    def option(self, key: str, path: bool = False) -> Any:
        """
        Return user specified action option.

        All option value access should go through this helper function, as
        it replaces relevant placeholders users might have specified.

        :param key: The key of the user option that should be retrieved.
        :param path: If True, convert string path to Path.is_absolute().
        :return: Processed action configuration value.
        """
        option_value = self._options.get(key)

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
            # substituted before it is returned.
            return self.replace(option_value)
        else:
            return option_value

    def _absolute_path(self, of: str) -> Path:
        """
        Return absolute path from relative string path.

        :param of: Relative path.
        :return: Absolute path anchored to `self.directory`.
        """
        return expand_path(
            path=Path(of),
            config_directory=self.directory,
        )

    @abc.abstractmethod
    def execute(self) -> Any:
        """Execute defined action."""

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

    def execute(self) -> None:
        """Import context section(s) according to user configuration block."""
        if self.null_object:
            # Null object does nothing
            return None

        insert_into(  # type: ignore
            context=self.context_store,
            from_config_file=self.option(key='from_path', path=True),
            section=self.option(key='to_section'),
            from_section=self.option(key='from_section'),
        )


class RequiredCompileDict(TypedDict):
    """Required fields of compile action."""

    template: str


class CompileDict(RequiredCompileDict, total=False):
    """Allowable fields of compile action."""

    target: str
    permissions: str


class CompileAction(Action):
    """Compile template action."""

    priority = 200

    def execute(self) -> Optional[Path]:
        """
        Compile template to target destination.

        :return: Path to compiled target.
        """
        if self.null_object:
            # Null objects do nothing
            return None

        template = self.option(key='template', path=True)
        target = self.option(key='target', path=True)
        if target is None:
            # A compilation target has not been specified, so we will compile
            # to a temporary file instead.
            target = self._create_temp_file(template.name)

        try:
            compiler.compile_template(
                template=template,
                target=target,
                context=self.context_store,
                shell_command_working_directory=self.directory,
                permissions=self.option(key='permissions'),
            )
        except TemplateNotFound:
            logger = logging.getLogger(__name__)
            logger.error(
                'Could not compile template '
                f'"{template}" to target "{target}". '
                'Template does not exist.',
            )
        return target

    def _create_temp_file(self, name) -> Path:
        """
        Create persisted tempory file.

        :return: Path object pointing to the created temporary file.
        """
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


class RunDict(TypedDict):
    """Required fields of run action user config."""

    shell: str
    timeout: Union[int, float]


class RunAction(Action):
    """Run shell command Action sub-class."""

    priority = 300

    def execute(self) -> Optional[Tuple[str, str]]:
        """
        Execute shell command action.

        :return: 2-tuple containing the executed command and its resulting
            stdout.
        """
        if self.null_object:
            # Null objects do nothing
            return None

        command = self.option(key='shell')
        timeout = self.option(key='timeout')
        result = utils.run_shell(
            command=command,
            timeout=timeout,
            working_directory=self.directory,
        )
        return command, result


class ActionBlockDict(TypedDict, total=False):
    """Valid keys in an action block."""

    import_context: Union[ImportContextDict, List[ImportContextDict]]
    compile: Union[CompileDict, List[CompileDict]]
    run: Union[RunDict, List[RunDict]]
    trigger: Union[str, List[str]]


class ActionBlockListDict(TypedDict, total=False):
    """
    Action block dict where everything is in lists.

    Users are allowed to not specify a list when they want to specify just
    *one* item. In this case the item is cast into a list in Module.__init__ in
    order to expect lists everywhere in the remaining methods.
    """

    import_context: List[ImportContextDict]
    compile: List[CompileDict]
    run: List[RunDict]
    trigger: List[str]


class ActionBlock:
    """
    Class representing a module action block, e.g. 'on_startup'.

    :param action_block: Dictinary containing all actions to be performed.
    :param directory: The directory used as anchor for relative paths. This
        must be an absolute path.
    :param replacer: Placeholder substitutor of string user options.
    :param context_store: A reference to the global context store.
    """

    _import_context_actions: List[ImportContextAction]
    _compile_actions: List[CompileAction]
    _run_actions: List[RunAction]

    def __init__(
        self,
        action_block: ActionBlockDict,
        directory: Path,
        replacer: Replacer,
        context_store: compiler.Context,
    ) -> None:
        """
        Construct ActionBlock object.

        Instantiates action types and appends to:
        self._run_actions: List[RunAction], and so on...
        """
        assert directory.is_absolute()
        self.action_block = action_block

        for identifier, action_type in (
            ('import_context', ImportContextAction),
            ('compile', CompileAction),
            ('run', RunAction),
        ):
            # Create and persist a list of all ImportContextAction objects
            action_configs = utils.cast_to_list(  # type: ignore
                self.action_block.get(identifier, {}),  # type: ignore
            )
            setattr(
                self,
                f'_{identifier}_actions',
                [action_type(  # type: ignore
                        options=action_config,
                        directory=directory,
                        replacer=replacer,
                        context_store=context_store,
                ) for action_config in action_configs
                ],
            )

    def import_context(self) -> None:
        """Import context into global context store."""
        for import_context_action in self._import_context_actions:
            import_context_action.execute()

    def compile(self) -> None:
        """Compile all templates."""
        for compile_action in self._compile_actions:
            compile_action.execute()

    def run(self) -> None:
        """Run shell commands."""
        for run_action in self._run_actions:
            run_action.execute()

    def execute(self) -> None:
        """
        Execute all actions in action block.

        The order of execution is:
            1) Perform all context imports into the context store.
            2) Compile all templates.
            3) Run all shell commands.
        """
        self.import_context()
        self.compile()
        self.run()
