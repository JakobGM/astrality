"""Test module for all behaviour related to the import_context action."""
import copy

from astrality.module import ModuleManager

def test_importing_all_context_sections_from_file(
    test_config_directory,
    default_global_options,
    _runtime,
):
    context_file = test_config_directory / 'context' / 'several_sections.yml'
    original_context = {
        'context/section2': {
            'k2_1': 'original_v2_1',
            'k2_2': 'original_v2_2',
        },
        'context/section3': {
            'k3_1': 'original_v3_1',
            'k3_2': 'original_v3_2',
        },
    }

    application_config = {
        'module/A': {
            'on_startup': {
                'import_context': [
                    {'from_path': str(context_file)}
                ]
            },
        },
    }
    application_config.update(copy.deepcopy(original_context))
    application_config.update(default_global_options)
    application_config.update(_runtime)

    module_manager = ModuleManager(application_config)

    # Assert that contents are equal, requiring some trickery, since the
    # application_context has been processed.
    assert len(module_manager.application_context) == len(original_context)
    for key, value in module_manager.application_context.items():
        assert value == original_context['context/' + key]

    # We expect the following context after import
    expected_context = {
        'context/section1': {
            'k1_1': 'v1_1',
            'k1_2': 'v1_2',
        },
        'context/section2': {
            'k2_1': 'v2_1',
            'k2_2': 'v2_2',
        },
        'context/section3': {
            'k3_1': 'original_v3_1',
            'k3_2': 'original_v3_2',
        },
    }

    # Now run startup actions, resulting in the file being imported
    module_manager.finish_tasks()

    # Assert that the new application_context is as expected
    assert len(module_manager.application_context) == len(expected_context)
    for key, value in module_manager.application_context.items():
        assert value == expected_context['context/' + key]
