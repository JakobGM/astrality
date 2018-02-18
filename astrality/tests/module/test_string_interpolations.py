"""Tests for string interpolations in ModuleManager class."""

from astrality.module import ModuleManager

def test_use_of_string_interpolations_of_module(
    default_global_options,
    _runtime,
):
    application_config = {
        'module/A': {
            'on_startup': {
                'compile': [
                    {'template': 'some/template'}
                ],
            },
        },
        'module/B': {
            'on_modified': {
                '/what/ever': {
                    'compile': [
                        {
                            'template': '/another/template',
                            'target': '/target/file',
                        },
                    ],
                },
            }
        },
    }
    application_config.update(default_global_options)
    application_config.update(_runtime)

    module_manager = ModuleManager(application_config)

    target1 = str(module_manager.templates['some/template'].target)
    target2 = '/target/file'

    string = 'one: {some/template} two: {/another/template}'
    interpolated_string = 'one: ' + target1 + ' two: ' + target2

    assert module_manager.interpolate_string(string) == interpolated_string
