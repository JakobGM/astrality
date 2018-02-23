from astrality.module import Module

def test_that_module_configuration_is_processed_correctly_before_use(
    test_config_directory,
):
    """
    Test that all list item configurations can be given as single strings,
    and that missing configuration options are inserted.
    """
    module_config = {'module/A': {
        'on_startup': {
            'run': 'echo hi!',
        },
        'on_event': {
            'import_context': {'from_file': '/test'},
            'run': ['echo 1', 'echo 2'],
            'trigger': 'on_modified:/some/file',
        },
        'on_modified': {
            '/some/file': {
                'compile': {'template': '/some/template'},
            },
        },
    }}

    module = Module(
        module_config=module_config,
        module_directory=test_config_directory,
    )

    processed_config = {
        'on_startup': {
            'run': ['echo hi!'],
            'compile': [],
            'import_context': [],
            'trigger': [],
        },
        'on_event': {
            'import_context': [{'from_file': '/test'}],
            'run': ['echo 1', 'echo 2'],
            'compile': [{'template': '/some/template'}],
            'trigger': ['on_modified:/some/file'],
        },
        'on_exit': {
            'run': [],
            'compile': [],
            'import_context': [],
            'trigger': [],
        },
        'on_modified': {
            '/some/file': {
                'compile': [{'template': '/some/template'}],
                'run': [],
                'import_context': [],
                'trigger': [],
            },
        },
    }
    assert module.module_config == processed_config

def test_that_all_context_files_are_correctly_identified(
    default_global_options,
    _runtime,
):
    # TODO
    pass
