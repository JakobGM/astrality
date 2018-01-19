from tempfile import NamedTemporaryFile, TemporaryDirectory
from typing import Any, Dict, Tuple
import os

import massedit


Config = Dict['str', Any]


def update_conky(
    config: Config,
    period: str,
) -> None:

    tempfiles = config['conky-temp-files']
    templates = config['conky-module-template']
    if period == 'night':
        os.system('sed -i "s/282828/CBCDFF/g" $XDG_CONFIG_HOME/conky/*.conf')
    else:
        os.system('sed -i "s/CBCDFF/282828/g" $XDG_CONFIG_HOME/conky/*.conf')


def generate_replacements(
    config: Config,
    period: str,
) -> Tuple[Replacement, ...]:
    """
    Given a configuration and the time of day, we can generate all the
    placeholders that could be present in the conky module templates and their
    respective replacements fitting for the time of day
    """
    templates = config['conky-module-templates']

    replacements = (
        Replacement(
            '${solarity:color:' + color_category + '}',
            period_colors[period]
        )
        for color_category, period_colors
        in config['colors'].items()
    )

    return replacements

def create_conky_temp_files(config: Config) -> Tuple[str, ...]:
    tempdir = TemporaryDirectory(prefix='solarity')
    print(f'Generating temporary conky files in: "{tempdir.name}"')

    temp_files = {}
    for conky_module_path in config['conky-module-paths']:
        temp_files[conky_module_path] = NamedTemporaryFile(
            prefix=conky_module_path,
            dir=tempdir.name,
        )

    return temp_files
