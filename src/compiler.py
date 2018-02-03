"""Module for compilation of templates."""

import logging
from pathlib import Path
from typing import Any, Dict, Union

from jinja2 import (
    Environment,
    FileSystemLoader,
    Undefined,
    make_logging_undefined,
)

from resolver import Resolver


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


def jinja_environment(templates_folder: Path) -> Environment:
    """Return a jinja Environment instance for templates in a folder."""
    logger = logging.getLogger(__name__)
    LoggingUndefined = make_logging_undefined(
        logger=logger,
        base=Undefined
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
    return env


def finalize_variable_expression(result: str) -> str:
    """Return empty strings for undefined template variables."""
    if result is None:
        return ''
    else:
        return result


def compile_template(
    template: Path,
    target: Path,
    context: Union[Dict[str, Any], Resolver],
) -> None:
    """Compile template to target destination with specific context."""
    logger.info(f'[Compiling] Template: "{template}" -> Target: "{target}"')

    env = jinja_environment(templates_folder=template.parent)
    jinja_template = env.get_template(name=template.name)
    result = jinja_template.render(context)

    with open(target, 'w') as target_file:
        target_file.write(result)
