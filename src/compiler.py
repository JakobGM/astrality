from pathlib import Path
from typing import Any, Dict, Set
import re

Config = Dict['str', Any]


def find_placeholders(string: str) -> set:
    placeholder_pattern = re.compile(r'\$\{solarity:[\w|\-^:]+:[\w|\-^:]+\}')
    return set(placeholder_pattern.findall(string))


def compile_template(
    template: Path,
    target: Path,
    period: str,
    config: Config,
) -> None:
    replacements = generate_replacements(config, period)
    replace = generate_replacer(replacements, period, config)

    print(f'[Compiling] Template: "{template}" -> Target: "{target}"')

    with open(template, 'r') as template_file:
        with open(target, 'w') as target_file:
            for line in template_file:
                target_file.write(replace(line))


def generate_replacements(
    config: Config,
    period: str,
) -> Dict[str, str]:
    """
    Given a configuration and the time of day, we can generate all the
    placeholders that could be present in the conky module templates and their
    respective replacements fitting for the time of day
    """
    templates = config['conky_module_templates']
    placeholders: Set[str] = set()
    for template_path in templates.values():
        with open(template_path, 'r') as template:
            for line in template:
                placeholders = placeholders | find_placeholders(line)

    replacements = {}
    for placeholder in placeholders:
        category, key = placeholder[11:-1].split(':')
        try:
            value = config[category][key]
            if category == 'colors':
                replacements[placeholder] = value[period]
            elif isinstance(value, str):
                replacements[placeholder] = value
        except KeyError:
            print('\033[91m')
            print(f'Invalid template tag "{placeholder}"')
            print('Replacing it with an empty string instead')
            replacements[placeholder] = ''
            print('\033[0m')

    return replacements


def generate_replacer(replacements: Dict[str, str], period: str, config: Config):
    """
    Given a set of replacements returned from generate_replacements() we can
    create a regex replacer which will replace these placeholders in string
    types
    """
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

