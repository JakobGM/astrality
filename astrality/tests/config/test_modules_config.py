"""Test module for global module configuration options."""
from pathlib import Path

import pytest

from astrality.exceptions import NonExistentEnabledModule
from astrality.config import (
    DirectoryModuleSource,
    EnabledModules,
    GithubModuleSource,
    GlobalModuleSource,
    GlobalModulesConfig,
    ModuleSource,
)

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

    assert modules_config.modules_directory == conf_path / 'modules'
    assert len(tuple(modules_config.external_module_sources)) == 4
    assert len(tuple(modules_config.external_module_config_files)) == 4


def test_custom_modules_folder(conf_path):
    modules_config = GlobalModulesConfig(
        config={'modules_directory': 'test_modules'},
        config_directory=conf_path,
    )

    assert modules_config.modules_directory == conf_path / 'test_modules'


def test_enabled_modules(test_config_directory):
    modules_config = GlobalModulesConfig({
        'modules_directory': 'test_modules',
        'enabled_modules': [
            {'name': 'oslo.*', 'safe': True},
            {'name': 'trondheim.*'},
        ],
    }, config_directory=test_config_directory)

    # Test that all ExternalModuleSource objects are created
    modules_directory_path = test_config_directory / 'test_modules'
    oslo_path = modules_directory_path / 'oslo'
    trondheim_path = modules_directory_path / 'trondheim'

    oslo = DirectoryModuleSource(
        enabling_statement={'name': 'oslo.*', 'trusted': True},
        modules_directory=modules_directory_path,
    )
    trondheim = DirectoryModuleSource(
        enabling_statement={'name': 'trondheim.*', 'trusted': False},
        modules_directory=modules_directory_path,
    )

    assert len(tuple(modules_config.external_module_sources)) == 2

    assert oslo in tuple(modules_config.external_module_sources)
    assert trondheim in tuple(modules_config.external_module_sources)

    # Test that all module config files are correctly set
    assert oslo_path / 'modules.yml' in modules_config.external_module_config_files
    assert trondheim_path / 'modules.yml' in modules_config.external_module_config_files

def test_external_module(test_config_directory):
    modules_directory_path = test_config_directory / 'test_modules'
    oslo = DirectoryModuleSource(
        enabling_statement={'name': 'oslo.*'},
        modules_directory=modules_directory_path,
    )

    oslo_path = test_config_directory / 'test_modules' / 'oslo'
    assert oslo.directory == oslo_path
    assert oslo.trusted == True
    assert oslo.category == 'oslo'
    assert oslo.config_file == oslo_path / 'modules.yml'


def test_retrieval_of_external_module_config(test_config_directory):
    external_module_source_config = {'name': 'burma.*'}
    external_module_source = DirectoryModuleSource(
        enabling_statement=external_module_source_config,
        modules_directory=test_config_directory / 'test_modules',
    )

    assert external_module_source.config == {
        f'module/burma.burma': {
            'enabled': True,
            'safe': False,
        },
    }


def test_retrieval_of_merged_module_configs(test_config_directory):
    modules_application_config = {
        'modules_directory': 'test_modules',
        'enabled_modules': [
            {'name': 'burma.burma'},
            {'name': 'thailand.thailand'},
        ],
    }
    modules_config = GlobalModulesConfig(
        config=modules_application_config,
        config_directory=test_config_directory,
    )
    burma_path = test_config_directory / 'test_modules' / 'burma'
    thailand_path = test_config_directory / 'test_modules' / 'thailand'

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


class TestModuleSource:

    def test_finding_correct_module_source_type_from_name(self):
        assert ModuleSource.type(of='name') == GlobalModuleSource
        assert ModuleSource.type(of='category.name') == DirectoryModuleSource
        assert ModuleSource.type(of='user/repo') == GithubModuleSource

    def test_detection_of_all_directories_within_a_directory(
        self,
        test_config_directory,
    ):
        assert tuple(EnabledModules.directory_names(
            within=test_config_directory / 'freezed_modules',
        )) == (
            'north_america',
            'south_america',
        )


class TestDirectoryModuleSource:
    """Test of object responsible for module(s) defined in a directory."""

    def test_which_enabling_statements_represents_directory_module_sources(self):
        assert DirectoryModuleSource.represented_by(
            module_name='category.name',
        )
        assert DirectoryModuleSource.represented_by(
            module_name='category.*',
        )
        assert not DirectoryModuleSource.represented_by(
            module_name='category.*not_valid',
        )
        assert not DirectoryModuleSource.represented_by(
            module_name='category.not_valid*',
        )
        assert not DirectoryModuleSource.represented_by(
            module_name='*.*',
        )
        assert not DirectoryModuleSource.represented_by(
            module_name='name',
        )
        assert not DirectoryModuleSource.represented_by(
            module_name='*',
        )

    def test_error_on_enabling_non_existent_module(
        self,
        test_config_directory,
    ):
        enabling_statement = {'name': 'north_america.colombia'}
        with pytest.raises(NonExistentEnabledModule):
            directory_module = DirectoryModuleSource(
                enabling_statement=enabling_statement,
                modules_directory=test_config_directory / 'freezed_modules',
            )

    def test_getting_config_dict_from_directory_module(
        self,
        test_config_directory,
    ):
        enabling_statement = {'name': 'north_america.USA'}
        directory_module = DirectoryModuleSource(
            enabling_statement=enabling_statement,
            modules_directory=test_config_directory / 'freezed_modules',
        )
        assert directory_module.config == {
            'module/north_america.USA': {
                'on_startup': {
                    'run': 'echo Greetings from the USA!',
                },
            },
            'context/geography': {
                'USA': {
                    'capitol': 'Washington D.C.',
                },
            },
        }

    def test_enabling_just_one_module_in_diretory(
        self,
        test_config_directory,
    ):
        enabling_statement = {'name': 'south_america.brazil'}
        directory_module = DirectoryModuleSource(
            enabling_statement=enabling_statement,
            modules_directory=test_config_directory / 'freezed_modules',
        )
        assert directory_module.config == {
            'module/south_america.brazil': {
                'on_startup': {
                    'run': 'echo Greetings from Brazil!',
                },
            },
            'context/geography': {
                'brazil': {
                    'capitol': 'Brasilia',
                },
                'argentina': {
                    'capitol': 'Buenos Aires',
                },
            },
        }

    def test_checking_if_directory_modules_contain_module_name(
        self,
        test_config_directory,
    ):
        enabling_statement = {'name': 'south_america.brazil'}
        directory_module = DirectoryModuleSource(
            enabling_statement=enabling_statement,
            modules_directory=test_config_directory / 'freezed_modules',
        )
        assert 'south_america.brazil' in directory_module

        assert 'south_america.argentina' not in directory_module
        assert 'brazil' not in directory_module
        assert 'argentina' not in directory_module


class TestGlobalModuleSource:

    def test_valid_names_which_indicate_globally_defined_modules(self):
        assert GlobalModuleSource.represented_by(
            module_name='module_name',
        )
        assert GlobalModuleSource.represented_by(
            module_name='*',
        )

        assert not GlobalModuleSource.represented_by(
            module_name='w*',
        )
        assert not GlobalModuleSource.represented_by(
            module_name='category.name',
        )
        assert not GlobalModuleSource.represented_by(
            module_name='category.*',
        )
        assert not GlobalModuleSource.represented_by(
            module_name='*.*',
        )
        assert not GlobalModuleSource.represented_by(
            module_name='jakobgm/module',
        )

    def test_that_enabled_modules_are_detected_correctly(self):
        global_module_source = GlobalModuleSource(
            enabling_statement={'name': 'enabled_module'},
            modules_directory=Path('/'),
        )
        assert 'enabled_module' in global_module_source
        assert 'disabled_module' not in global_module_source
        assert '*' not in global_module_source

    def test_that_wildcard_global_enabling_enables_all_global_modules(self):
        global_module_source = GlobalModuleSource(
            enabling_statement={'name': '*'},
            modules_directory=Path('/'),
        )
        assert 'enabled_module1' in global_module_source
        assert 'enabled_module2' in global_module_source

        assert 'directory.module' not in global_module_source
        assert 'user/repo' not in global_module_source


class TestGithubModuleSource:

    def test_valid_names_which_indicate_globally_defined_modules(self):
        assert GithubModuleSource.represented_by(
            module_name='jakobgm/astrality',
        )
        assert GithubModuleSource.represented_by(
            module_name='user_name./repo-git.ast',
        )

        assert not GithubModuleSource.represented_by(
            module_name='w*',
        )
        assert not GithubModuleSource.represented_by(
            module_name='category.name',
        )
        assert not GithubModuleSource.represented_by(
            module_name='category.*',
        )
        assert not GithubModuleSource.represented_by(
            module_name='*.*',
        )
        assert not GithubModuleSource.represented_by(
            module_name='*',
        )
        assert not GithubModuleSource.represented_by(
            module_name='global_module',
        )

    def test_that_username_and_repo_is_identified(self, test_config_directory):
        github_module_source = GithubModuleSource(
            enabling_statement={'name': 'jakobgm/astrality'},
            modules_directory=test_config_directory / 'test_modules',
        )
        assert github_module_source.github_user == 'jakobgm'
        assert github_module_source.github_repo == 'astrality'

    def test_that_enabled_repos_are_found(self, test_config_directory):
        github_module_source = GithubModuleSource(
            enabling_statement={'name': 'jakobgm/astrality'},
            modules_directory=test_config_directory / 'test_modules',
        )
        assert 'jakobgm/astrality' in github_module_source

        assert 'jakobgm/another_repo' not in github_module_source
        assert 'astrality' not in github_module_source
        assert 'jakobgm' not in github_module_source


class TestEnabledModules:

    def test_processing_of_enabled_statements(
        self,
        test_config_directory,
    ):
        enabled_modules = EnabledModules([], Path('/'), Path('/'))

        assert enabled_modules.process_enabling_statements(
            enabling_statements=[
                {'name': '*.*'}
            ],
            modules_directory=test_config_directory / 'freezed_modules',
        ) == [{'name': 'north_america.*'}, {'name': 'south_america.*'}]
        assert enabled_modules.all_directory_modules_enabled == True
        assert enabled_modules.all_global_modules_enabled == False


    def test_enabled_detection(
        self,
        test_config_directory,
        caplog,
    ):
        enabling_statements = [
            {'name': 'global'},
            {'name': 'south_america.*'},
            {'name': 'jakobgm/color_schemes.astrality'},
            {'name': 'invalid_syntax]][['},
        ]
        enabled_modules = EnabledModules(
            enabling_statements=enabling_statements,
            config_directory=test_config_directory,
            modules_directory=test_config_directory / 'freezed_modules',
        )
        for sources in enabled_modules.source_types.values():
            assert len(sources) == 1
        assert len(caplog.record_tuples) == 1

        assert 'global' in enabled_modules
        assert 'south_america.brazil' in enabled_modules
        assert 'south_america.argentina' in enabled_modules
        assert 'jakobgm/color_schemes.astrality' in enabled_modules

        assert 'not_enabled' not in enabled_modules
        assert 'non_existing_folder.non_existing_module' not in enabled_modules
        assert 'user/not_enabled' not in enabled_modules

    def test_enabled_detection_with_global_wildcard(self):
        enabling_statements = [
            {'name': '*'},
        ]
        enabled_modules = EnabledModules(
            enabling_statements=enabling_statements,
            config_directory=Path('/'),
            modules_directory=Path('/'),
        )

        assert 'global' in enabled_modules
        assert 'whatever' in enabled_modules

        assert 'south_america.brazil' not in enabled_modules
        assert 'south_america.argentina' not in enabled_modules
        assert 'jakobgm/color_schemes.astrality' not in enabled_modules
