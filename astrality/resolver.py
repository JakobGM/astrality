from math import inf
from numbers import Number
from typing import (
    Any,
    Dict,
    ItemsView,
    KeysView,
    ValuesView,
    Optional,
    Tuple,
    Union,
)


Real = Union[int, float]
Key = Union[str, Real]
Value = Any


class Resolver:
    """
    Dictionary-like object which specifies application configuration options.

    It also tries resolves access to missing integer indexed keys if a lesser
    integer key exists.

    An example of its functionality:
    replacements = Resolver({
    'colors': {1: 'CACCFD', 2: 'BACBEB'}
    })
    replacements[1]
    >>> 'CACCFD'
    replacements[2]
    >>> 'BACBEB'
    replacements[3]
    >>> 'BACBEB'
    """
    _dict: Union['Resolver', Dict[Key, Value]]

    def __init__(
        self,
        content: Optional[Union['Resolver', dict]] = None,
    ) -> None:
        """
        Initialize a configuration file from source object.

        The source object can either be a dictionary or another Resolver object.
        If not given an argument, an empty Resolver object is initialized.
        """

        if isinstance(content, (Resolver, dict,)):
            self.update(content)
        elif content is not None:
            raise ValueError('Resolver initialized with wrong argument type.')

        # Determine the greatest number index inserted
        self._max_key: Real = float(-inf)
        if hasattr(self, '_dict'):
            for key in self._dict.keys():
                if isinstance(key, Number):
                    self._max_key = max(key, self._max_key)

    def __eq__(self, other) -> bool:
        """Check if content is identical to other Resolver or dictionary."""

        if hasattr(self, '_dict'):
            return self._dict.__eq__(other)
        else:
            return {}.__eq__(other)

    def __req__(self, other) -> bool:
        """Right side comparison, see self.__eq__()."""
        return self.__eq__(other)

    def __setitem__(self, key: Key, value: Value) -> None:
        """Insert `value` into the `key` index."""

        if not hasattr(self, '_dict'):
            self._dict: Dict[Key, Value] = {}

        if isinstance(key, Number):
            self._max_key = max(key, self._max_key)

        if isinstance(value, dict):
            self._dict[key] = Resolver(value)
        else:
            self._dict[key] = value

    def __getitem__(self, key: Key) -> Value:
        """
        Get item inserted into `key` index, with integer index resolution.

        Here "integer index resolution" means that if you try to retrieve
        non-existent integer index 2, it will retrieve the greatest available
        integer indexed value instead.
        """

        if not hasattr(self, '_dict'):
            raise KeyError('Tried to access key from empty Resolver section')

        try:
            # Return excact hit if present
            return self._dict[key]

        except KeyError as key_error:
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

    def __repr__(self) -> str:
        """Return human-readable representation of Resolver object."""
        if hasattr(self, '_dict'):
            return f'Resolver({self._dict.__repr__()})'
        else:
            return 'Resolver(' + {}.__repr__() + ')'

    def __str__(self) -> str:
        """Return string representation of Resolver object."""
        if hasattr(self, '_dict'):
            return f'Resolver({self._dict.__str__()})'
        else:
            return 'Resolver(' + {}.__str__() + ')'

    def __len__(self) -> int:
        """Return the number of key inserted into the Resolver object."""

        return self._dict.__len__()

    def __contains__(self, key: Key) -> bool:
        return self._dict.__contains__(key)

    def items(self) -> ItemsView[Key, Value]:
        if hasattr(self, '_dict'):
            return self._dict.items()
        else:
            return {}.items()

    def keys(self) -> KeysView[Key]:
        """Return all keys which have been inserted into the Resolver object."""
        if hasattr(self, '_dict'):
            return self._dict.keys()
        else:
            return {}.keys()

    def values(self) -> ValuesView[Value]:
        """Return all values inserted into the Resolver object."""
        if hasattr(self, '_dict'):
            return self._dict.values()
        else:
            return {}.values()

    def update(self, other: Union['Resolver', dict]) -> None:
        """Overwrite all items from other onto the Resolver object."""

        if isinstance(other, (Resolver, dict,)):
            # Populate internal data structure from dictionary
            if not hasattr(self, '_dict'):
                self._dict = Resolver()

            for key, value in other.items():
                self._dict[key] = value

        else:
            raise NotImplementedError(
                f'Resolver.update() not yet implemented for type {type(other)})'
            )
