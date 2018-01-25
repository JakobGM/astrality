from configparser import ConfigParser
from math import inf
from typing import Any, Dict, Optional, Tuple, Union


class Resolver:
    """
    Dictionary-like object which specifies application configuration options.

    It also tries resolves access to integer indexed keys if a lesser integer
    key exists. These integer keys are still represented as strings.

    An example of its functionality:
    replacements = Resolver({
    'colors': {'1': 'CACCFD', '2': 'BACBEB'}
    })
    replacements['1']
    >>> 'CACCFD'
    replacements['2']
    >>> 'BACBEB'
    replacements['3']
    >>> 'BACBEB'
    """

    def __init__(
        self,
        content: Optional[Union[ConfigParser, dict]] = None,
    ) -> None:
        """
        Initialize a configuration file from source object.

        The source object can either be a ConfigParser object which has already
        .read() a configuration file, a dictionary, or if not given an
        argument, an empty Resolver object is initialized.
        """

        if isinstance(content, (ConfigParser, dict,)):
            self.update(content)
        elif content is not None:
            raise ValueError('Resolver initialized with wrong argument type.')

        # Determine the greatest "string integer" index inserted
        self._max_key = -inf
        if hasattr(self, '_dict'):
            for key in self._dict.keys():
                try:
                    self._max_key = max(int(key), self._max_key)
                except ValueError:
                    pass

    def __eq__(self, other) -> bool:
        """Check if content is identical to other Resolver or dictionary."""

        if hasattr(self, '_dict'):
            return self._dict.__eq__(other)
        else:
            return {}.__eq__(other)

    def __req__(self, other) -> bool:
        """Right side comparison, see self.__eq__()."""
        return self.__eq__(other)

    def __setitem__(self, key: str, value: str) -> None:
        """Insert `value` into the `key` index."""
        if not hasattr(self, '_dict'):
            self._dict: Dict[str, Union[str, dict]] = {}

        try:
            self._max_key = max(int(key), self._max_key)
        except ValueError as e:
            if 'invalid literal for int() with base 10' in str(e):
                pass
            else:
                raise

        if isinstance(value, dict):
            self._dict[key] = Resolver(value)
        else:
            self._dict[key] = value

    def __getitem__(self, key: Any) -> Any:
        """
        Get item inserted into `key` index, with integer index resolution.

        Here "integer index resolution" means that if you try to retrieve
        non-existent "string integer" index '2', it will retrieve the greatest
        "string integer" available instead.
        """
        if not hasattr(self, '_dict'):
            raise KeyError('Tried to access key from empty Resolver section')

        try:
            # Return excact hit if present
            return self._dict[key]

        except KeyError as key_error:
            # The key is not present. See if we can resolve the use of another
            # one through integer key priority
            if self._max_key > -inf:
                # Another integer key has been inserted earlier
                try:
                    int(key)
                    # We can return the max integer key previously inserted
                    return self._dict[str(self._max_key)]

                except ValueError as value_error:
                    if 'invalid literal for int() with base 10' in str(value_error):
                        # The key is not representable as an integer, so we
                        # have a normal KeyError exception on our hands. Raise
                        # the originally caught KeyError again.
                        raise key_error
                    else:
                        # Throwing any other ValueErrors just in case
                        raise
            else:
                raise KeyError(f'Integer index "{key}" is non-existent and had '
                               'no lower index to be substituted for')


    def get(self, key, defualt=None) -> Any:
        """Get value from index with fallback value `default`."""
        try:
            return self.__getitem__(key)
        except KeyError:
            return defualt

    def __repr__(self) -> str:
        """Return human-readable representation of Resolver object."""
        if hasattr(self, '_dict'):
            return self._dict.__repr__()
        else:
            return {}.__repr__()

    def __str__(self) -> str:
        """Return string representation of Resolver object."""
        if hasattr(self, '_dict'):
            return self._dict.__str__()
        else:
            return {}.__str__()

    def items(self):
        if hasattr(self, '_dict'):
            return self._dict.items()
        else:
            return {}.items()

    def keys(self) -> Tuple[str]:
        """Return all keys which have been inserted into the Resolver object."""
        if hasattr(self, '_dict'):
            return self._dict.keys()
        else:
            return {}.keys()

    def values(self):
        """Return all values inserted into the Resolver object."""
        if hasattr(self, '_dict'):
            return self._dict.values()
        else:
            return {}.values()

    def update(self, other: Union[ConfigParser, dict]) -> None:
        """Overwrite all items from other onto the Resolver object."""

        if isinstance(other, ConfigParser):
            # Populate internal data structure from ConfigParser object
            if not hasattr(self, '_dict'):
                self._dict = {}

            for section_name, section in other.items():
                self._dict[section_name] = Resolver()
                for key, value in section.items():
                    self._dict[section_name][key] = value

        elif isinstance(other, (Resolver, ConfigParser, dict,)):
            # Populate internal data structure from dictionary
            if not hasattr(self, '_dict'):
                self._dict = Resolver()

            for key, value in other.items():
                self._dict[key] = value

        else:
            raise NotImplementedError(
                f'Resolver.update() not yet implemented for type {type(other)})'
            )
