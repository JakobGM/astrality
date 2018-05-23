"""Module defining Context class for templating context handling."""

from math import inf
from numbers import Number
from pathlib import Path
import logging
from typing import (
    Any,
    Dict,
    ItemsView,
    Iterable,
    KeysView,
    ValuesView,
    Optional,
    Union,
)

from astrality import utils


Real = Union[int, float]
Key = Union[str, Real]
Value = Any


class Context:
    """
    Dictionary-like object whith integer index resolution.

    An example of its functionality:
    >>> replacements = Context({
    >>> 'colors': {1: 'CACCFD', 2: 'BACBEB'}
    >>> })
    replacements['colors'][1]
    >>> 'CACCFD'
    replacements['colors'][2]
    >>> 'BACBEB'
    replacements['colors'][3]
    >>> 'BACBEB'
    """

    _dict: Dict[Key, Value]

    def __init__(
        self,
        content: Optional[Union['Context', dict, Path]] = None,
    ) -> None:
        """
        Contstruct context object.

        :param content: Either dictionar, Context or Path object. If Path, then
            content is compiled as a YAML template and imported.
            If not given an argument, an empty Context object is initialized.
        """
        self._dict = {}
        self._max_key: Real = float(-inf)

        if isinstance(content, (dict, Context)):
            self.update(content)
        elif isinstance(content, Path):
            if content.is_file():
                self.import_context(from_path=content)
            elif (content / 'context.yml').is_file():
                self.import_context(from_path=content / 'context.yml')
        elif content is not None:
            raise ValueError('Context initialized with wrong argument type.')

        # Determine the greatest number index inserted
        for key in self._dict.keys():
            if isinstance(key, Number):
                self._max_key = max(key, self._max_key)

    def import_context(
        self,
        from_path: Path,
        from_section: Optional[str] = None,
        to_section: Optional[str] = None,
    ) -> None:
        """
        Insert context values from yml file.

        :param from_path: Path to .yml file or directory containing
            "context.yml".
        :param from_section: If given, only import specific section from path.
        :param to_section: If given, rename from_section to to_section.
        """
        new_context = utils.compile_yaml(
            path=from_path,
            context=self,
        )

        logger = logging.getLogger(__name__)
        if from_section is None and to_section is None:
            logger.info(
                f'[import_context] All sections from "{from_path}".',
            )
            self.update(new_context)
        elif from_section and to_section:
            logger.info(
                f'[import_context] Section "{from_section}" from "{from_path}" '
                f'into section "{to_section}".',
            )
            self[to_section] = new_context[from_section]
        else:
            assert from_section
            logger.info(
                f'[import_context] Section "{from_section}" '
                f'from "{from_path}" ',
            )
            self[from_section] = new_context[from_section]

    def __eq__(self, other) -> bool:
        """Check if content is identical to other Context or dictionary."""
        if isinstance(other, Context):
            return self._dict == other._dict
        elif isinstance(other, dict):
            return self._dict == other
        else:
            raise RuntimeError(
                f'Context comparison with unknown type "{type(other)}"',
            )

    def __setitem__(self, key: Key, value: Value) -> None:
        """Insert `value` into the `key` index."""
        if isinstance(key, Number):
            self._max_key = max(key, self._max_key)

        if isinstance(value, dict):
            # Insterted dictionaries are cast to Context instances
            self._dict[key] = Context(value)
        else:
            self._dict[key] = value

    def __getitem__(self, key: Key) -> Value:
        """
        Get item inserted into `key` index, with integer index resolution.

        Here "integer index resolution" means that if you try to retrieve
        non-existent integer index 2, it will retrieve the greatest available
        integer indexed value instead.
        """
        try:
            # Return excact hit if present
            return self._dict[key]
        except KeyError:
            # The key is not present. See if we can resolve the use of another
            # one through integer key priority.
            if self._max_key > -inf:
                # Another integer key has been inserted earlier
                if isinstance(key, Number):
                    # We can return the max integer key previously inserted
                    return self._dict[self._max_key]
                else:
                    # Throwing any other ValueErrors just in case
                    raise
            else:
                raise KeyError(f'Integer index "{key}" is non-existent and had '
                               'no lower index to be substituted for')

    def get(self, key: Key, defualt=None) -> Value:
        """Get value from index with fallback value `default`."""
        try:
            return self.__getitem__(key)
        except KeyError:
            return defualt

    def __iter__(self) -> Iterable[Value]:
        """Return iterable of Context object."""
        return self._dict.__iter__()

    def __repr__(self) -> str:
        """Return human-readable representation of Context object."""
        return f'Context({self._dict.__repr__()})'

    def __str__(self) -> str:
        """Return string representation of Context object."""
        return f'Context({self._dict.__str__()})'

    def __len__(self) -> int:
        """Return the number of key inserted into the Context object."""
        return self._dict.__len__()

    def __contains__(self, key: Key) -> bool:
        """Return true if `key` is inserted into Context object."""
        return self._dict.__contains__(key)

    def items(self) -> ItemsView[Key, Value]:
        """Return all key, value pairs of the Context object."""
        return self._dict.items()

    def keys(self) -> KeysView[Key]:
        """Return all keys which have been inserted into the Context object."""
        return self._dict.keys()

    def values(self) -> ValuesView[Value]:
        """Return all values inserted into the Context object."""
        return self._dict.values()

    def update(self, other: Union['Context', dict]) -> None:
        """Overwrite all items from other onto the Context object."""
        for key, value in other.items():
            self.__setitem__(key, value)

    def copy(self) -> 'Context':
        """Return shallow copy of context."""
        return Context(self._dict.copy())

    def reverse_update(self, other: Union['Context', dict]) -> None:
        """Update context while preserving conflicting keys."""
        other_copy = other.copy()
        other_copy.update(self._dict)
        self.update(other_copy)
