"""Test module for the use of external modules."""
import pytest

from astrality.module import ModuleManager

def test_that_external_modules_are_brought_in(
    test_config_directory,
    default_global_options,
    _runtime,
):
    application_config = {
        'config/modules': {'enabled': [{
            'name': 'thailand',
        }]},
        'module/cambodia': {
            'enabled': True,
        },
    }
    application_config.update(default_global_options)
    application_config.update(_runtime)

    module_manager = ModuleManager(application_config)

    thailand_path = test_config_directory / 'modules' / 'thailand'
    assert tuple(module_manager.modules.keys()) == (
        f'thailand[{thailand_path}]',
        'cambodia',
    )
