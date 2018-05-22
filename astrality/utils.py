"""General utility functions which are used across the application."""

import logging
import re
import shutil
import subprocess
from functools import partial
from io import StringIO
from pathlib import Path
from typing import Any, Dict, List, TypeVar, Union

from yaml import dump, load  # noqa

from astrality import compiler
from astrality.context import Context


logger = logging.getLogger(__name__)

# Try to import PyYAML library for faster YAML parsing
try:
    from yaml import CLoader as Loader, CDumper as Dumper  # type: ignore
    logger.info('Using LibYAML bindings for faster .yml parsing.')
except ImportError:  # pragma: no cover
    from yaml import Loader, Dumper
    logger.warning(
        'LibYAML not installed.'
        'Using somewhat slower pure python implementation.',
    )


def run_shell(
    command: str,
    timeout: Union[int, float] = 2,
    fallback: Any = '',
    working_directory: Path = Path.home(),
    allow_error_codes: bool = False,
    log_success: bool = True,
) -> str:
    """
    Return the standard output of a shell command.

    If the shell command has a non-zero exit code or times out, the function
    returns the `fallback` argument instead of the standard output.

    :param command: Shell command to be executed.
    :param timeout: How long to wait for return of command.
    :param fallback: Default return value on timeout/error codes.
    :param working_directory: Command working directory.
    :param allow_error_codes: If error codes should return fallback.
    :param log_success: If successful commands stdout should be logged.
    :return: Stdout of command, or `fallback` on error/timeout.
    """
    process = subprocess.Popen(
        command,
        cwd=working_directory,
        shell=True,
        universal_newlines=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        # We add just a small extra wait in case users specify 0 seconds,
        # in order to not print an error when a command is really quick.
        if timeout == 0:
            process.wait(timeout=0.1)
        else:
            process.wait(timeout=timeout)

        for error_line in process.stderr:
            logger.error(str(error_line))

        if process.returncode != 0 and not allow_error_codes:
            logger.error(
                f'Command "{command}" exited with non-zero return code: ' +
                str(process.returncode),
            )
            return fallback
        else:
            stdout = process.communicate()[0].strip('\n')
            if log_success and stdout:
                logger.info(stdout)
            return stdout

    except subprocess.TimeoutExpired:
        if timeout == 0:
            return fallback

        logger.warning(
            f'The command "{command}" used more than {timeout} seconds in '
            'order to finish. The exit code can not be verified. This might be '
            'intentional for background processes and daemons.',
        )
        return fallback


T = TypeVar('T')


def cast_to_list(content: Union[T, List[T]]) -> List[T]:
    """
    Cast content to a 1-item list containing content.

    If content already is a list, return content unaltered.
    """
    if not isinstance(content, list):
        return [content]
    else:
        return content


def resolve_targets(
    content: Path,
    target: Path,
    include: str,
) -> Dict[Path, Path]:
    """
    Return content/target file path pairs.

    If `content` is a directory, it returns content/target path pairs that
    reflects `content`s file hierarchy at the `target` directory.

    If `content` is a file, and `target` is an existing directory, the target
    will become `content` within the `target`.

    Content files that do not match the include regex string are discarded.
    Any capture group in the regex string is used for renaming the target.

    :param content: Source path, either file or directory.
    :param target: Target path, either file or directory.
    :param include: Regular expression string for filtering/renaming content.
    :return: Dictionary with content file keys and target file values.
    """
    targets: Dict[Path, Path] = {}
    if content.is_file():
        if target.is_dir():
            targets[content] = target / content.name
        else:
            targets[content] = target

    else:
        for file in content.glob('**/*'):
            if file.is_dir():
                continue
            target_file = target / file.relative_to(content)
            targets[file] = target_file

    include_pattern = re.compile(include)
    filtered_targets: Dict[Path, Path] = {}
    for content_file, target_file in targets.items():
        match = include_pattern.fullmatch(target_file.name)
        if not match:
            continue

        # If there is no group match, keep the name, else, use last group
        renamed_target_file = target_file.parent \
            / match.group(match.lastindex or 0)
        filtered_targets[content_file] = renamed_target_file

    return filtered_targets


def compile_yaml(
    path: Path,
    context: Context,
) -> Dict:
    """
    Return datastructure from compiled YAML jinja2 template.

    :param path: YAML template file path.
    :param context: Jinja2 context.
    """
    if not path.is_file():  # pragma: no cover
        error_msg = f'Could not load config file "{path}".'
        logger.critical(error_msg)
        raise FileNotFoundError(error_msg)

    config_string = compiler.compile_template_to_string(
        template=path,
        context=context,
        shell_command_working_directory=path.parent,
    )

    return load(StringIO(config_string), Loader=Loader)


def load_yaml(path: Path) -> Any:
    """
    Load content from YAML file.

    :param path: Path to YAML formatted file.
    :return: Contents of YAML file.
    """
    with open(path, 'r') as yaml_file:
        return load(yaml_file.read(), Loader=Loader)


def dump_yaml(path: Path, data: Dict) -> None:
    """
    Dump data to yaml file.

    :param path: Path to file to be created.
    :param data: Data to be dumped to file.
    """
    str_data = yaml_str(data)
    with open(path, 'w') as yaml_file:
        yaml_file.write(str_data)


def yaml_str(data: Any) -> str:
    """
    Return YAML string representation of data.

    :param data: Data to be converted to YAML string format.
    :return: YAML string representation of python data structure.
    """
    return dump(
        data,
        Dumper=Dumper,
        default_flow_style=False,
    )


def copy(
    source: Union[str, Path],
    destination: Union[str, Path],
    follow_symlinks=True,
) -> None:
    """
    Copy source path content to destination path.

    :param source: Path to content to be copied.
    :param destination: New path for content.
    :param follow_symlinks: If True, symlinks are resolved before copying.
    """
    shutil.copy2(
        src=str(source),
        dst=str(destination),
        follow_symlinks=follow_symlinks,
    )


def move(
    source: Union[str, Path],
    destination: Union[str, Path],
    follow_symlinks=True,
) -> None:
    """
    Move source path content to destination path.

    :param source: Path to content to be moved.
    :param destination: New path for content.
    :param follow_symlinks: If True, symlinks are resolved before moving.
    """
    shutil.move(
        src=str(source),
        dst=str(destination),
        copy_function=partial(
            copy,
            follow_symlinks=follow_symlinks,
        ),
    )
