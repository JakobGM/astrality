"""Module for compilation of templates."""

import logging
import os
from functools import partial
from pathlib import Path
from typing import Any, Dict, Optional, Union

from jinja2 import (
    Environment,
    FileSystemLoader,
    Undefined,
    make_logging_undefined,
)

from astrality.utils import generate_expanded_env_dict
from astrality.resolver import Resolver
from astrality.utils import run_shell


Context = Dict[str, Resolver]
ApplicationConfig = Dict[str, Dict[str, Any]]

logger = logging.getLogger('astrality')


def cast_to_numeric(value: str) -> Union[int, float, str]:
    """Casts string to numeric type if possible, else return string."""
    try:
        return int(value)
    except ValueError:
        try:
            return float(value)
        except ValueError:
            return value


def context(config: ApplicationConfig) -> Context:
    """
    Return a context dictionary based on the contents of a config dict.

    Only sections named context/* are considered to be context sections, and
    these sections are returned with 'context/' stripped away, and with their
    contents cast to a Resolver instance.
    """
    contents: Context = {}
    for section_name, section in config.items():
        if not isinstance(section_name, str) or \
           not len(section_name) > 8 or \
           not section_name[:8].lower() == 'context/':
            continue
        else:
            category = section_name[8:]
            contents[category] = Resolver(section)

    return contents


def jinja_environment(
    templates_folder: Path,
    shell_command_working_directory: Path,
) -> Environment:
    """Return a jinja Environment instance for templates in a folder."""
    logger = logging.getLogger(__name__)
    LoggingUndefined = make_logging_undefined(
        logger=logger,
        base=Undefined,
    )

    env = Environment(
        loader=FileSystemLoader(
            str(templates_folder),
            followlinks=True,
        ),
        autoescape=False,
        auto_reload=True,
        optimized=True,
        finalize=finalize_variable_expression,
        undefined=LoggingUndefined,
    )

    # Add env context containing all environment variables
    env.globals['env'] = generate_expanded_env_dict()

    # Add run shell command filter
    run_shell_from_working_directory = partial(
        run_shell,
        working_directory=shell_command_working_directory,
    )
    env.filters['shell'] = run_shell_from_working_directory

    return env


def finalize_variable_expression(result: str) -> str:
    """Return empty strings for undefined template variables."""
    if result is None:
        return ''
    else:
        return result


def compile_template_to_string(
    template: Path,
    context: Context,
    shell_command_working_directory: Optional[Path] = None,
) -> str:
    """
    Return the compiled template string.

    Context placeholder replacements given by `context`, and shell filters
    run with working directory ``shell_command_working_directory``.
    """
    if not shell_command_working_directory:
        shell_command_working_directory = template.parent

    env = jinja_environment(
        templates_folder=template.parent,
        shell_command_working_directory=shell_command_working_directory,
    )
    jinja_template = env.get_template(name=template.name)

    return jinja_template.render(context)


def compile_template(
    template: Path,
    target: Path,
    context: Context,
    shell_command_working_directory: Path,
) -> None:
    """Compile template to target destination with specific context."""
    logger.info(f'[Compiling] Template: "{template}" -> Target: "{target}"')

    result = compile_template_to_string(
        template=template,
        context=context,
        shell_command_working_directory=shell_command_working_directory,
    )

    # Create parent directories if they do not exist
    os.makedirs(target.parent, exist_ok=True)

    with open(target, 'w') as target_file:
        target_file.write(result)
