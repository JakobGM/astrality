"""
Module defining class-representation of module actions.

Each action class type encapsulates the user specified options available for
that specific action type. The action itself can be performed by invoking the
object method `execute()`.
"""

import abc
from pathlib import Path
from typing import Callable, Optional, Union

from mypy_extensions import TypedDict

from .compiler import Context
from .config import expand_path, insert_into

Replacer = Callable[[str], str]


class Action(abc.ABC):
    """
    Superclass for module action types.

    :param options: A dictionary containing the user options for a given module
                    action type.
    :param directory: The directory used as anchor for relative paths. This
                      must be an absolute path.
    :param replacer: Placeholder substitution of string user options.
    """

    directory: Path
    priority: int
    replace: Replacer

    def __init__(
        self,
        options: Union['ImportContextDict', 'CompileDict', 'RunDict'],
        directory: Path,
        replacer: Replacer,
        **kwargs,
    ) -> None:
        """Contstruct action object."""
        assert directory.is_absolute()
        self.options = options
        self.directory = directory
        self.replace = replacer  # type: ignore

    @abc.abstractmethod
    def execute(self) -> None:
        """Exucute defined action."""

    def absolute_path(self, of: str) -> Path:
        """
        Return absolute path of relative string path.

        Expands relative paths relative to self.directory.
        """
        return expand_path(
            path=Path(of),
            config_directory=self.directory,
        )


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
    from_path: Path
    from_section: Optional[str]
    to_section: Optional[str]
    context_store: Context

    def __init__(
        self,
        options: ImportContextDict,
        directory: Path,
        replacer: Replacer,
        context_store: Context,
    ) -> None:
        """
        Contstruct import_context action object.

        Expands any relative paths relative to `self.directory`.
        """
        super().__init__(options, directory, replacer)
        self.from_path = self.absolute_path(of=self.options['from_path'])
        self.from_section = self.options.get('from_section')
        self.to_section = self.options.get('to_section')
        self.context_store = context_store

    def execute(self) -> None:
        """Import context section(s) according to user configuration block."""
        insert_into(
            context=self.context_store,
            from_config_file=self.from_path,
            section=self.to_section,
            from_section=self.from_section,
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

    def __init__(
        self,
        options: CompileDict,
        directory: Path,
        replacer: Callable[[str], str],
    ) -> None:
        """Initialize compile action."""


class RunDict(TypedDict):
    """Required fields of run action user config."""

    command: str


class RunAction(Action):
    """Run shell command action."""

    priority = 300

    def __init__(
        self,
        options: RunDict,
        directory: Path,
        replacer: Callable[[str], str],
    ) -> None:
        """Initialize shell command action."""
