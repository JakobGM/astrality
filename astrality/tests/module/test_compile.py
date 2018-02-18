"""Tests for everything related to module compile actions."""
import os
from pathlib import Path

import pytest

from astrality.module import ModuleManager, WatchedFile

@pytest.yield_fixture
def compiling_fixtures(
    default_global_options,
    _runtime,
    test_config_directory,
):
    """Return a set of fixtures required to inspect template compilation."""
    fixtures = {}

    fixtures['template1'] = Path('template1')
    fixtures['template2'] = Path('template2')
    fixtures['template2_target'] = Path('template2_target')
    fixtures['template3'] = Path('template3')
    fixtures['template4'] = Path('template4')

    application_config = {
        'module/A': {
            'on_startup': {
                'compile': [
                    {
                        'template': str(fixtures['template1']),
                    },
                    {
                        'template': str(fixtures['template2']),
                        'target': str(fixtures['template2_target']),
                    },
                ],
            },
        },
        'module/B': {
            'on_modified': {
                str(fixtures['template3']): {
                    'run': ['echo template3 touched'],
                    'compile': [
                        {
                            'template': str(fixtures['template4']),
                        },
                    ],
                },
            },
        },
    }
    application_config.update(default_global_options)
    application_config.update(_runtime)
    fixtures['application_config'] = application_config

    module_manager = ModuleManager(application_config)
    fixtures['module_manager'] = module_manager

    yield fixtures

    if fixtures['template2_target'].is_file():
        os.remove(fixtures['template2_target'])

    module_manager.exit()


def test_that_module_manager_detects_all_managed_templates(
    compiling_fixtures,
    test_config_directory,
):
    """Test that all compiled templates are identified."""

    module_manager = compiling_fixtures['module_manager']
    template1 = compiling_fixtures['template1']
    template2 = compiling_fixtures['template2']
    template4 = compiling_fixtures['template4']

    template2_target = compiling_fixtures['template2_target']

    expected_templates = {
        str(template1): test_config_directory / template1,
        str(template2): test_config_directory / template2,
        str(template4): test_config_directory / template4,
    }
    for specified_path, absolute_path in expected_templates.items():
        assert module_manager.templates[specified_path].source == absolute_path

    assert module_manager.templates[str(template2)].target == \
        test_config_directory / template2_target

def test_module_manager_placeholders_are_correctly_generated(
    compiling_fixtures,
    test_config_directory,
):
    """Test that placeholders are generated."""
    module_manager = compiling_fixtures['module_manager']

    template2 = compiling_fixtures['template2']
    template2_target = compiling_fixtures['template2_target']

    string_replacements = module_manager.string_replacements

    assert string_replacements[str(template2)] == str(
        test_config_directory / template2_target,
    )

def test_that_all_modified_observed_files_are_identified(
    compiling_fixtures,
    test_config_directory,
):
    """Test that all files watched for modifications are correctly identified."""
    module_manager = compiling_fixtures['module_manager']
    specified_path = compiling_fixtures['template3']
    path = test_config_directory / specified_path
    module = module_manager.modules['B']

    assert module_manager.on_modified_paths == {
        path: WatchedFile(
            path=path,
            module=module,
            specified_path=str(specified_path),
        )
    }
