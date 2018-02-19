from astrality.module import Module

def test_that_all_arguments_are_converted_to_lists():
    """
    Test that all list item configurations can be given as single strings.
    """
    module_config = {'module/A': {
        'on_startup': {
            'run': 'echo hi!',
        },
        'on_event': {
            'import_context': {'from_file': '/test'},
            'run': ['echo 1', 'echo 2'],
        },
        'on_modified': {
            '/some/file': {
                'compile': {'template': '/some/template'},
            },
        },
    }}

    module = Module(module_config)

    processed_config = {
        'on_startup': {
            'run': ['echo hi!'],
            'compile': [],
            'import_context': [],
        },
        'on_event': {
            'import_context': [{'from_file': '/test'}],
            'run': ['echo 1', 'echo 2'],
            'compile': [],
        },
        'on_exit': {
            'run': [],
            'compile': [],
            'import_context': [],
        },
        'on_modified': {
            '/some/file': {
                'compile': [{'template': '/some/template'}],
                'run': [],
                'import_context': [],
            },
        },
    }
    assert module.module_config == processed_config
