"""Tests for module requirements."""

import logging
from pathlib import Path

from astrality.module import Module
from astrality.tests.utils import RegexCompare

def test_module_requires_option(caplog):
    """Test that modules are disabled when they don't satisfy `requires`."""
    # Simple module that satisfies the requirements
    does_satisfy_requiremnets = { 'module/satisfies': {
        'enabled': True,
        'requires': {'shell': 'command -v cd',},
    }}
    assert Module.valid_class_section(
        section=does_satisfy_requiremnets,
        requires_timeout=1,
        requires_working_directory=Path('/'),
    )


    # Simple module that does not satisfy requirements
    does_not_satisfy_requirements = { 'module/does_not_satisfy': {
        'requires': {'shell': 'command -v does_not_exist',},
    }}
    assert not Module.valid_class_section(
        section=does_not_satisfy_requirements,
        requires_timeout=1,
        requires_working_directory=Path('/'),
    )
    assert (
        'astrality',
        logging.WARNING,
        '[module/does_not_satisfy] Module requirements: '
        'Unsuccessful command: "command -v does_not_exist", !',
    ) in caplog.record_tuples


    # Test failing one of many requirements
    does_not_satisfy_one_requirement = { 'module/does_not_satisfy': {
        'requires': [
            {'shell': 'command -v cd',},
            {'shell': 'command -v does_not_exist',},
        ],
    }}
    caplog.clear()
    assert not Module.valid_class_section(
        section=does_not_satisfy_one_requirement,
        requires_timeout=1,
        requires_working_directory=Path('/'),
    )
    assert (
        'astrality',
        logging.WARNING,
        RegexCompare(
            '\[module/does_not_satisfy\] Module requirements: .+ '
            'Unsuccessful command: "command -v does_not_exist", !',
        )
    ) in caplog.record_tuples
