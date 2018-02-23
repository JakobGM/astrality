"""Test module for global module configuration options."""
import pytest

from astrality.config import GlobalModulesConfig, ExternalModuleSource

@pytest.fixture
def modules_application_config():
    return {
        'modules_directory': 'test_modules',
        'enabled_modules': [
            {'name': 'oslo', 'safe': False},
            {'name': 'trondheim'},
        ],
    }


def test_default_options_for_modules(conf_path):
    modules_config = GlobalModulesConfig({}, config_directory=conf_path)

    assert modules_config.modules_directory_path == conf_path / 'modules'
    assert len(tuple(modules_config.external_module_sources)) == 0
    assert len(tuple(modules_config.external_module_config_files)) == 0


def test_custom_modules_folder(conf_path):
    modules_config = GlobalModulesConfig(
        config={'modules_directory': 'test_modules'},
        config_directory=conf_path,
    )

    assert modules_config.modules_directory_path == conf_path / 'test_modules'


def test_enabled_modules(conf_path):
    modules_config = GlobalModulesConfig({
        'enabled_modules': [
            {'name': 'oslo', 'safe': True},
            {'name': 'trondheim'},
        ],
    }, config_directory=conf_path)

    # Test that all ExternalModuleSource objects are created
    modules_directory_path = conf_path / 'modules'
    oslo_path = conf_path / 'modules' / 'oslo'
    trondheim_path = conf_path / 'modules' / 'trondheim'

    oslo = ExternalModuleSource(
        config={'name': 'oslo', 'safe': True},
        config_directory=conf_path,
        modules_directory_path=modules_directory_path,
    )
    trondheim = ExternalModuleSource(
        config={'name': 'trondheim', 'safe': False},
        config_directory=conf_path,
        modules_directory_path=modules_directory_path,
    )

    assert len(tuple(modules_config.external_module_sources)) == 2

    assert oslo in tuple(modules_config.external_module_sources)
    assert trondheim in tuple(modules_config.external_module_sources)

    # Test that all module config files are correctly set
    assert oslo_path / 'modules.yaml' in modules_config.external_module_config_files
    assert trondheim_path / 'modules.yaml' in modules_config.external_module_config_files

def test_external_module(conf_path):
    modules_directory_path = conf_path / 'modules'
    oslo = ExternalModuleSource(
        config={'name': 'oslo'},
        config_directory=conf_path,
        modules_directory_path=modules_directory_path,
    )

    oslo_path = conf_path / 'modules' / 'oslo'
    assert oslo.directory == oslo_path
    assert oslo.safe == False
    assert oslo.name == 'oslo'
    assert oslo.config_file == oslo_path / 'modules.yaml'


def test_retrieval_of_external_module_config(test_config_directory):
    external_module_source_config = {'name': 'burma'}
    external_module_source = ExternalModuleSource(
        config=external_module_source_config,
        modules_directory_path=test_config_directory / 'modules',
        config_directory=test_config_directory,
    )

    assert external_module_source.module_config_dict() == {
        f'module/burma.burma': {
            'enabled': True,
            'safe': False,
        },
    }


def test_retrieval_of_merged_module_configs(test_config_directory):
    modules_application_config = {
        'enabled_modules': [
            {'name': 'burma'},
            {'name': 'thailand'},
        ],
    }
    modules_config = GlobalModulesConfig(
        config=modules_application_config,
        config_directory=test_config_directory,
    )
    burma_path = test_config_directory / 'modules' / 'burma'
    thailand_path = test_config_directory / 'modules' / 'thailand'

    assert modules_config.module_configs_dict() == {
        f'module/burma.burma': {
            'enabled': True,
            'safe': False,
        },
        f'module/thailand.thailand': {
            'enabled': True,
            'safe': True,
        },
    }
