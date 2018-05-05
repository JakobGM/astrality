"""Test module for all behaviour related to the import_context action."""
from astrality.context import Context


def test_importing_all_context_sections_from_file(
    test_config_directory,
    action_block_factory,
    module_factory,
    module_manager_factory,
):
    context_file = test_config_directory / 'context' / 'several_sections.yml'
    original_context = Context({
        'section2': {
            'k2_1': 'original_v2_1',
            'k2_2': 'original_v2_2',
        },
        'section3': {
            'k3_1': 'original_v3_1',
            'k3_2': 'original_v3_2',
        },
    })

    import_context = action_block_factory(
        import_context={'from_path': str(context_file)},
    )
    module = module_factory(on_startup=import_context)
    module_manager = module_manager_factory(module, context=original_context)
    assert module_manager.application_context == original_context

    # We expect the following context after import
    expected_context = Context({
        'section1': {
            'k1_1': 'v1_1',
            'k1_2': 'v1_2',
        },
        'section2': {
            'k2_1': 'v2_1',
            'k2_2': 'v2_2',
        },
        'section3': {
            'k3_1': 'original_v3_1',
            'k3_2': 'original_v3_2',
        },
    })

    # Now run startup actions, resulting in the file being imported
    module_manager.finish_tasks()

    # Assert that the new application_context is as expected
    assert module_manager.application_context == expected_context
