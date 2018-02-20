from math import inf
from numbers import Number
from typing import (
    Any,
    Dict,
    ItemsView,
    Iterable,
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
    Dictionary-like object whith integer index resolution.

    An example of its functionality:
    replacements = Resolver({
    'colors': {1: 'CACCFD', 2: 'BACBEB'}
    })
    replacements['colors'][1]
    >>> 'CACCFD'
    replacements['colors'][2]
    >>> 'BACBEB'
    replacements['colors'][3]
    >>> 'BACBEB'
    """
    _dict: Union['Resolver', Dict[Key, Value]]

    def __init__(
        self,
        content: Optional[Union['Resolver', dict]] = None,
    ) -> None:
        """
        Initialize a Resolver instance from another Resolver or dictionary.

        If not given an argument, an empty Resolver object is initialized.
        """
        self._dict = {}
        self._max_key: Real = float(-inf)

        if isinstance(content, (Resolver, dict,)):
            self.update(content)
        elif content is not None:
            raise ValueError('Resolver initialized with wrong argument type.')

        # Determine the greatest number index inserted
        for key in self._dict.keys():
            if isinstance(key, Number):
                self._max_key = max(key, self._max_key)

    def __eq__(self, other) -> bool:
        """Check if content is identical to other Resolver or dictionary."""
        if isinstance(other, Resolver):
            return self._dict == other._dict
        elif isinstance(other, dict):
            return self._dict == other
        else:
            raise RuntimeError(
                f'Resolver comparison with unknown type "{type(other)}"',
            )

    def __setitem__(self, key: Key, value: Value) -> None:
        """Insert `value` into the `key` index."""
        if isinstance(key, Number):
            self._max_key = max(key, self._max_key)

        if isinstance(value, dict):
            # Insterted dictionaries are cast to Resolver instances
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

    def __iter__(self) -> Iterable[Value]:
        """Return iterable of Resolver object."""
        return self._dict.__iter__()

    def __repr__(self) -> str:
        """Return human-readable representation of Resolver object."""
        return f'Resolver({self._dict.__repr__()})'

    def __str__(self) -> str:
        """Return string representation of Resolver object."""
        return f'Resolver({self._dict.__str__()})'

    def __len__(self) -> int:
        """Return the number of key inserted into the Resolver object."""
        return self._dict.__len__()

    def __contains__(self, key: Key) -> bool:
        """Return true if `key` is inserted into Resolver object."""
        return self._dict.__contains__(key)

    def items(self) -> ItemsView[Key, Value]:
        """Return all key, value pairs of the Resolver object."""
        return self._dict.items()

    def keys(self) -> KeysView[Key]:
        """Return all keys which have been inserted into the Resolver object."""
        return self._dict.keys()

    def values(self) -> ValuesView[Value]:
        """Return all values inserted into the Resolver object."""
        return self._dict.values()

    def update(self, other: Union['Resolver', dict]) -> None:
        """Overwrite all items from other onto the Resolver object."""
        for key, value in other.items():
            self.__setitem__(key, value)
