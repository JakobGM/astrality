from collections import namedtuple
from tempfile import NamedTemporaryFile, TemporaryDirectory
from typing import Any, Dict, Tuple
import re
import os

import massedit


Config = Dict['str', Any]


def update_conky(
    config: Config,
    period: str,
) -> None:
    replacements = generate_replacements(config, period)
    tempfiles = config['conky-temp-files']
    templates = config['conky-module-templates']

    for module, template_path in templates:
        with open(template_path, 'r') as template:
            with open(tempfiles[module], 'w') as target:
                for line in template:
                    target.write(line.replace(replacements))


    if period == 'night':
        os.system('sed -i "s/282828/CBCDFF/g" $XDG_CONFIG_HOME/conky/*.conf')
    else:
        os.system('sed -i "s/CBCDFF/282828/g" $XDG_CONFIG_HOME/conky/*.conf')


def generate_replacements(
    config: Config,
    period: str,
) -> Dict[str, str]:
    """
    Given a configuration and the time of day, we can generate all the
    placeholders that could be present in the conky module templates and their
    respective replacements fitting for the time of day
    """
    templates = config['conky-module-templates']

    replacements = {
        '${solarity:color:' + color_category + '}': period_colors[period]
        for color_category, period_colors
        in config['colors'].items()
    }

    return replacements

def generate_replacer(replacements: Dict[str, str]):
    """
    Given a set of replacements returned from generate_replacements() we can
    create a regex replacer which will replace these placeholders in string
    types
    """
    # We have to escape the placeholder pattern in case of use of reserved
    # characters
    replacements = {
        re.escape(placeholder): replacement
        for placeholder, replacement in replacements.items()
    }

    # Create a regex pattern from the placeholders
    pattern = re.compile("|".join(replacements.keys()))

    def replacer(text):
        # Source: https://stackoverflow.com/a/6117124
        return pattern.sub(lambda m: replacements[re.escape(m.group(0))], text)

    return replacer


def create_conky_temp_files(config: Config) -> Tuple[str, ...]:
    temp_files = {}
    for conky_module_path in config['conky-module-paths']:
        temp_files[conky_module_path] = NamedTemporaryFile(
            prefix=conky_module_path,
            dir='/tmp/solarity'
        )

    return temp_files
