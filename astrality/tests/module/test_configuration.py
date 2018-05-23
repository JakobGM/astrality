"""Tests for configuraition dictionary management."""
import shutil

import pytest

from astrality.module import GlobalModulesConfig, ModuleManager


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
    for source in global_modules_config.external_module_sources:
        source.modules({})

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
    for source in global_modules_config.external_module_sources:
        source.modules({})

    assert 'burma::burma' in global_modules_config.enabled_modules
    assert 'india' in global_modules_config.enabled_modules
    assert 'burma::only_defined_accepted' \
        not in global_modules_config.enabled_modules


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
    for source in global_modules_config.external_module_sources:
        source.modules({})

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


def test_enabling_of_modules_defined_different_places():
    application_config = {
        'modules': {
            'modules_directory': 'freezed_modules',
            'enabled_modules': [
                {'name': 'south_america::brazil'},
                {'name': 'india'},
            ],
        },
    }
    modules = {
        'india': {},     # Enabled
        'pakistan': {},  # Not enabled
    }
    module_manager = ModuleManager(
        config=application_config,
        modules=modules,
    )

    assert len(module_manager.modules) == 2
    assert 'south_america::brazil' in module_manager.modules
    assert 'india' in module_manager.modules


def test_enabling_of_all_modules():
    application_config = {
        'modules': {
            'modules_directory': 'freezed_modules',
        },
    }

    modules = {
        'india': {},     # Enabled
        'pakistan': {},  # Not enabled
    }

    module_manager = ModuleManager(
        config=application_config,
        modules=modules,
    )

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


@pytest.mark.slow
def test_using_three_different_module_sources(
    test_config_directory,
    delete_jakobgm,
):
    modules_directory = test_config_directory / 'freezed_modules'

    application_config = {
        'modules': {
            'modules_directory': str(modules_directory),
            'enabled_modules': [
                {'name': 'north_america::*'},
                {'name': 'github::jakobgm/test-module.astrality'},
                {'name': 'italy'},
            ],
        },
    }

    modules = {
        'italy': {},
        'spain': {},
    }
    module_manager = ModuleManager(
        config=application_config,
        modules=modules,
    )

    assert len(module_manager.modules) == 4
    assert 'north_america::USA' in module_manager.modules
    assert 'github::jakobgm/test-module.astrality::botswana' \
        in module_manager.modules
    assert 'github::jakobgm/test-module.astrality::ghana' \
        in module_manager.modules
    assert 'italy' in module_manager.modules
