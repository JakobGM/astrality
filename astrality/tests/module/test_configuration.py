import shutil

import pytest

from astrality.module import GlobalModulesConfig, Module, ModuleManager

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


def test_modules_config_explicitly_enabled_modules(
    test_config_directory,
):
    global_modules_config_dict = {
        'modules_directory': 'test_modules',
        'enabled_modules': [
            {'name': 'burma::burma'},
            {'name': 'india'},
        ],
    }
    global_modules_config = GlobalModulesConfig(
        config=global_modules_config_dict,
        config_directory=test_config_directory,
    )
    global_modules_config.compile_config_files({})

    assert 'burma::burma' in global_modules_config.enabled_modules
    assert 'india' in global_modules_config.enabled_modules
    assert 'whatever' not in global_modules_config.enabled_modules


def test_modules_config_implicitly_enabled_modules(
    test_config_directory,
):
    global_modules_config_dict = {
        'modules_directory': 'test_modules',
        'enabled_modules': [
            {'name': 'burma::*'},
            {'name': 'india'},
        ],
    }
    global_modules_config = GlobalModulesConfig(
        config=global_modules_config_dict,
        config_directory=test_config_directory,
    )
    global_modules_config.compile_config_files({})

    assert 'burma::burma' in global_modules_config.enabled_modules
    assert 'india' in global_modules_config.enabled_modules
    assert 'burma::only_defined_accepted' not in global_modules_config.enabled_modules

def test_modules_config_several_implicitly_enabled_modules(
    test_config_directory,
):
    global_modules_config_dict = {
        'modules_directory': 'test_modules',
        'enabled_modules': [
            {'name': 'two_modules::*'},
            {'name': 'india'},
        ],
    }
    global_modules_config = GlobalModulesConfig(
        config=global_modules_config_dict,
        config_directory=test_config_directory,
    )
    global_modules_config.compile_config_files({})

    assert 'two_modules::bhutan' in global_modules_config.enabled_modules
    assert 'two_modules::bangladesh' in global_modules_config.enabled_modules

def test_modules_config_where_all_modules_are_enabled(
    test_config_directory,
):
    global_modules_config_dict = {
        'modules_directory': str(test_config_directory / 'test_modules'),
        'enabled_modules': [
            {'name': '*::*'},
            {'name': '*'},
        ],
    }
    global_modules_config = GlobalModulesConfig(
        config=global_modules_config_dict,
        config_directory=test_config_directory,
    )
    global_modules_config.compile_config_files(
        {'module': {'setting': 'whatever'}},
    )

    assert 'two_modules::bhutan' in global_modules_config.enabled_modules
    assert 'two_modules::bangladesh' in global_modules_config.enabled_modules


def test_enabling_of_modules_defined_different_places(
    default_global_options,
    _runtime,
):
    application_config = {
        'config/modules': {
            'modules_directory': 'freezed_modules',
            'enabled_modules': [
                {'name': 'south_america::brazil'},
                {'name': 'india'},
            ],
        },
        'module/india': {},     # Enabled
        'module/pakistan': {},  # Not enabled
    }
    application_config.update(default_global_options)
    application_config.update(_runtime)

    module_manager = ModuleManager(application_config)

    assert len(module_manager.modules) == 2
    assert 'south_america::brazil' in module_manager.modules
    assert 'india' in module_manager.modules

def test_enabling_of_all_modules(
    default_global_options,
    _runtime,
):
    application_config = {
        'config/modules': {
            'modules_directory': 'freezed_modules',
        },
        'module/india': {},     # Enabled
        'module/pakistan': {},  # Not enabled
    }
    application_config.update(default_global_options)
    application_config.update(_runtime)

    module_manager = ModuleManager(application_config)

    assert len(module_manager.modules) == 5
    assert 'india' in module_manager.modules
    assert 'pakistan' in module_manager.modules
    assert 'north_america::USA' in module_manager.modules
    assert 'south_america::brazil' in module_manager.modules
    assert 'south_america::argentina' in module_manager.modules


@pytest.yield_fixture
def delete_jakobgm(test_config_directory):
    """Delete jakobgm module directory used in testing."""
    location = test_config_directory / 'freezed_modules' / 'jakobgm'

    yield

    if location.is_dir():
        shutil.rmtree(location)

def test_using_three_different_module_sources(
    default_global_options,
    _runtime,
    test_config_directory,
    delete_jakobgm,
):
    modules_directory = test_config_directory / 'freezed_modules'

    application_config = {
        'config/modules': {
            'modules_directory': str(modules_directory),
            'enabled_modules': [
                {'name': 'north_america::*'},
                {'name': 'github::jakobgm/test-module.astrality'},
                {'name': 'italy'},
            ],
        },
        'module/italy': {},
        'module/spain': {},
    }
    application_config.update(default_global_options)
    application_config.update(_runtime)

    module_manager = ModuleManager(application_config)

    assert len(module_manager.modules) == 4
    assert 'north_america::USA' in module_manager.modules
    assert 'github::jakobgm/test-module.astrality::botswana' in module_manager.modules
    assert 'github::jakobgm/test-module.astrality::ghana' in module_manager.modules
    assert 'italy' in module_manager.modules
