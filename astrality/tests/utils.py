"""Module for test utilities."""

import re
import time
from typing import Any, Callable, Union


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
        # Object only comparable with string
        assert isinstance(other, str)
        return bool(self.pattern.fullmatch(other))

    def __repr__(self) -> str:
        """Return string representation of RegexCompare object."""
        return f'RegexCompare({self.pattern})'


class Retry:
    """
    Class for retrying tests.

    :param expression: Zero arity callable which should return True after some
        retries.
    :param tries: Number of attempts.
    :param delay: Seconds to sleep between each attempt.
    :param increase_delay: Increase delay for each attempt.
    """

    def __init__(
        self,
        tries: int = 10,
        delay: Union[int, float] = 0.1,
        increase_delay: Union[int, float] = 0.3,
    ) -> None:
        """Retry object constructor."""
        self.tries = tries
        self.delay = delay
        self.increase = increase_delay

    def __call__(self, expression: Callable[[], Any]) -> bool:
        """
        Retry callable until it returns a truthy value.

        :param expression: Zero arity callable returning truhty/falsy values.
        """
        attempt = 0
        while attempt < self.tries:
            attempt += 1
            try:
                result = expression()
                if result:
                    return result
            except BaseException:
                pass

            time.sleep(self.delay)
            self.delay += self.increase  # type: ignore

        return expression()
