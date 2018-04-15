"""Tests for everything related to module compile actions."""
import os
from pathlib import Path

import pytest

from astrality.module import ModuleManager

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
