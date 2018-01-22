from collections import namedtuple
from pathlib import Path
import subprocess
from tempfile import NamedTemporaryFile
from typing import Set
from typing import Any, Dict, Tuple
import re
import os

Config = Dict['str', Any]


def compile_conky_templates(
    config: Config,
    period: str,
) -> None:
    tempfiles = config['conky_temp_files']
    templates = config['conky_module_templates']

    for module, template_path in templates.items():
        compile_template(
            template=Path(template_path),
            target=Path(tempfiles[module].name),
            period=period,
            config=config,
        )


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


def find_placeholders(string: str) -> set:
    placeholder_pattern = re.compile(r'\$\{solarity:[\w|\-^:]+:[\w|\-^:]+\}')
    return set(placeholder_pattern.findall(string))


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
        value = config[category][key]
        if category == 'colors':
            replacements[placeholder] = value[period]
        elif isinstance(value, str):
            replacements[placeholder] = value
        else:
            raise RuntimeError(f'Invalid template tag "{placeholder}"')

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


def create_conky_temp_files(config: Config) -> Tuple[str, ...]:
    # NB: These temporary files/directories need to be persisted during the
    # entirity of the scripts runtime, since the files are deleted when they
    # go out of scope
    temp_dir_path = os.path.join(os.environ.get('TMPDIR', '/tmp'), 'solarity')
    config['temp_directory'] = temp_dir_path
    if not os.path.isdir(temp_dir_path):
        os.mkdir(temp_dir_path)

    return {
        module: NamedTemporaryFile(
            prefix=module + '-',
            dir=temp_dir_path
        )
        for module, path
        in config['conky_module_paths'].items()
    }

def start_conky_process(config: Config) -> None:
    conky_temp_files = config['conky_temp_files']
    for module_path, file in conky_temp_files.items():
        print(f'Initializing conky module "{module_path}"')
        print(f'    Tempory file placed at "{file.name}"')
        subprocess.Popen(['conky', '-c', file.name])

def exit_conky(config: Config) -> None:
    os.system('killall conky')
