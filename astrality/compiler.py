"""Module for compilation of templates."""

import logging
import os
import shutil
from functools import partial
from pathlib import Path
from typing import Any, Dict, Optional

from jinja2 import (
    Environment,
    FileSystemLoader,
    Undefined,
    make_logging_undefined,
)

from astrality import utils
from astrality.context import Context

ApplicationConfig = Dict[str, Dict[str, Any]]
logger = logging.getLogger(__name__)


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
    env.globals['env'] = os.environ

    # Add run shell command filter
    run_shell_from_working_directory = partial(
        utils.run_shell,
        working_directory=shell_command_working_directory,
        log_success=False,
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
    permissions: Optional[str] = None,
) -> None:
    """
    Compile template to target destination with specific context.

    If `permissions` is provided, the target file will have its file mode set
    accordingly.
    permissions='755' -> chmod 755
    permissions='u+x' -> chmod u+x
    """
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

    # Copy template's file permissions to compiled target file
    shutil.copymode(template, target)

    if permissions:
        result = utils.run_shell(
            command=f'chmod {permissions} {target}',
            timeout=0,
            fallback=False,
        )

        if result is False:
            logger.error(
                f'Could not set "{permissions}" permissions for "{target}"',
            )
