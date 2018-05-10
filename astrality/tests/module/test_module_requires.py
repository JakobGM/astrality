"""Tests for module requirements."""

import logging
from pathlib import Path

from astrality.module import Module, ModuleManager
from astrality.tests.utils import RegexCompare


def test_module_requires_option(caplog):
    """Test that modules are disabled when they don't satisfy `requires`."""
    # Simple module that satisfies the requirements
    does_satisfy_requiremnets = {
        'enabled': True,
        'requires': {'shell': 'command -v cd'},
    }
    assert Module.valid_module(
        name='satisfies',
        config=does_satisfy_requiremnets,
        requires_timeout=1,
        requires_working_directory=Path('/'),
    )

    # Simple module that does not satisfy requirements
    does_not_satisfy_requirements = {
        'requires': {'shell': 'command -v does_not_exist'},
    }
    assert not Module.valid_module(
        name='does_not_satisfy',
        config=does_not_satisfy_requirements,
        requires_timeout=1,
        requires_working_directory=Path('/'),
    )
    assert (
        'astrality.module',
        logging.WARNING,
        '[module/does_not_satisfy] Module requirements: '
        'Unsuccessful command: "command -v does_not_exist", !',
    ) in caplog.record_tuples

    # Test failing one of many requirements
    does_not_satisfy_one_requirement = {
        'requires': [
            {'shell': 'command -v cd'},
            {'shell': 'command -v does_not_exist'},
        ],
    }
    caplog.clear()
    assert not Module.valid_module(
        name='does_not_satisfy',
        config=does_not_satisfy_one_requirement,
        requires_timeout=1,
        requires_working_directory=Path('/'),
    )
    assert (
        'astrality.module',
        logging.WARNING,
        RegexCompare(
            r'\[module/does_not_satisfy\] Module requirements: .+ '
            'Unsuccessful command: "command -v does_not_exist", !',
        ),
    ) in caplog.record_tuples


def test_module_module_dependencies():
    """ModuleManager should remove modules with missing module dependencies."""
    config = {
        'modules': {
            'modules_directory': 'freezed_modules',
            'enabled_modules': [
                {'name': 'north_america::*'},
                {'name': 'A'},
                {'name': 'B'},
                {'name': 'C'},
            ],
        },
    }
    modules = {
        'A': {'requires': {'module': 'north_america::USA'}},
        'B': {'requires': [{'module': 'A'}]},
        'C': {'requires': [{'module': 'D'}]},
    }

    module_manager = ModuleManager(
        config=config,
        modules=modules,
    )
    assert sorted(module_manager.modules.keys()) \
        == sorted(['A', 'B', 'north_america::USA'])
