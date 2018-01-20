from collections import namedtuple
import shutil
from stat import S_IRUSR,S_IWUSR,S_IRGRP,S_IWGRP,S_IROTH,S_IWOTH
import subprocess
from tempfile import NamedTemporaryFile, TemporaryDirectory
from typing import Any, Dict, Tuple
import re
import os

import massedit


Config = Dict['str', Any]


def compile_conky_templates(
    config: Config,
    period: str,
) -> None:
    replacements = generate_replacements(config, period)
    replace = generate_replacer(replacements)

    tempfiles = config['conky-temp-files']
    templates = config['conky-module-templates']

    for module, template_path in templates.items():
        with open(template_path, 'r') as template:
            with open(tempfiles[module].name, 'w') as target:
                for line in template:
                    target.write(replace(line))


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
        '${solarity:colors:' + color_category + '}': period_colors[period]
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
    # NB: These temporary files/directories need to be persisted during the
    # entirity of the scripts runtime, since the files are deleted when they
    # go out of scope
    temp_dir_path = os.environ.get('TMPDIR', '/tmp') + '/solarity'
    config['temp-directory'] = temp_dir_path
    if not os.path.isdir(temp_dir_path):
        os.mkdir(temp_dir_path)

    return {
        module: NamedTemporaryFile(
            prefix=module + '-',
            dir=temp_dir_path
        )
        for module, path
        in config['conky-module-paths'].items()
    }

def start_conky_process(config: Config) -> None:
    conky_temp_files = config['conky-temp-files']
    for module_path, file in conky_temp_files.items():
        print(f'Initializing conky module "{module_path}"')
        print(f'    Tempory file placed at "{file.name}"')
        subprocess.Popen(['conky', '-c', file.name])

def exit_conky(config: Config) -> None:
    os.system('killall conky')
