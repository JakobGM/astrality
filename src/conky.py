from pathlib import Path
import subprocess
from tempfile import NamedTemporaryFile
from typing import Any, Dict, Tuple
import os

from compiler import compile_template

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
