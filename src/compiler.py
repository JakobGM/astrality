from pathlib import Path
import logging
from typing import Callable, Dict, Set, Union
import re

from resolver import Resolver

logger = logging.getLogger('astrality')


def find_placeholders(string: str) -> Set[str]:
    """Return all astrality placeholders present in `string`."""

    placeholder_pattern = re.compile(r'\$\{ast:[\w|\-^:]+:[\w|\-^:]+\}')
    return set(placeholder_pattern.findall(string))


def compile_template(
    template: Path,
    target: Path,
    config: Resolver,
) -> None:
    """
    Compile template based on contents of a given configuration.

    All instances of ${ast:section:option} is replaced with the value in
    config[section][option].
    """

    replacements = generate_replacements(template, config)
    replace = generate_replacer(replacements)

    logger.info(f'[Compiling] Template: "{template}" -> Target: "{target}"')

    with open(template, 'r') as template_file:
        with open(target, 'w') as target_file:
            for line in template_file:
                target_file.write(replace(line))


def generate_replacements(template: Path, config: Resolver) -> Dict[str, str]:
    """
    Return dictionary defining all placeholder -> replacement mappings.

    The function only generates mappings for the placeholders present in in the
    template file.
    """

    # Find all placeholders present in the template file
    placeholders: Set[str] = set()
    with open(template, 'r') as template_file:
        for line in template_file:
            placeholders = placeholders | find_placeholders(line)

    # Find all corresponding replacement values from the configuration
    replacements: Dict[str, str] = {}
    for placeholder in placeholders:
        section, option = placeholder[6:-1].split(':')
        try:
            replacements[placeholder] = str(config[section][cast_to_numeric(option)])
        except KeyError:
            logger.error(f'Invalid template tag "{placeholder}"'
                         'Replacing it with an empty string instead')
            replacements[placeholder] = ''

    return replacements


def generate_replacer(replacements: Dict[str, str]) -> Callable[[str], str]:
    """Return function that replaces placeholders with fitting values."""

    # We have to escape the placeholder patterns in case of use of reserved
    # regex characters
    escaped_placeholders = (
        re.escape(placeholder)
        for placeholder in replacements.keys()
    )

    # Compile all the placeholders which are present in our file into on single
    # pattern
    pattern = re.compile("|".join(escaped_placeholders))

    def replace(template: str):
        return pattern.sub(
            lambda match: replacements[match.group(0)],
            template,
        )

    return replace

def cast_to_numeric(value: str) -> Union[int, float, str]:
    """Casts string to numeric type if possible, else return string."""

    try:
        return int(value)
    except ValueError:
        try:
            return float(value)
        except ValueError:
            return value
