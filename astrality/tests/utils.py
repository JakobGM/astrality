"""Module for test utilities."""

import re

class RegexCompare:
    """
    Class for creating regex objects which can be compared with strings.

    :param regex: Regex string pattern"
    """
    def __init__(self, regex: str) -> None:
        """Constructor for RegexCompare object."""
        self.pattern = re.compile(regex)

    def __eq__(self, other) -> bool:
        """Return True if full regex match."""
        if not isinstance(other, str):
            return False
        else:
            return bool(self.pattern.fullmatch(other))

    def __repr__(self) -> str:
        """Return string representation of RegexCompare object."""
        return f'RegexCompare({self.pattern})'
