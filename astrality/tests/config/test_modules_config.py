"""Test module for global module configuration options."""
import shutil
import time
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
from astrality.utils import run_shell

@pytest.fixture
def modules_application_config():
    return {
        'modules_directory': 'test_modules',
        'enabled_modules': [
            {'name': 'oslo', 'safe': False},
            {'name': 'trondheim'},
        ],
    }


@pytest.yield_fixture(autouse=True)
def delete_jakobgm(test_config_directory):
    """Delete jakobgm module directory used in testing."""
    location1 = test_config_directory / 'freezed_modules' / 'jakobgm'
    location2 = test_config_directory / 'test_modules' / 'jakobgm'

    yield

    if location1.is_dir():
        shutil.rmtree(location1)
    if location2.is_dir():
        shutil.rmtree(location2)


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
            {'name': 'oslo::*', 'safe': True},
            {'name': 'trondheim::*'},
        ],
    }, config_directory=test_config_directory)

    # Test that all ExternalModuleSource objects are created
    modules_directory_path = test_config_directory / 'test_modules'
    oslo_path = modules_directory_path / 'oslo'
    trondheim_path = modules_directory_path / 'trondheim'

    oslo = DirectoryModuleSource(
        enabling_statement={'name': 'oslo::*', 'trusted': True},
        modules_directory=modules_directory_path,
    )
    trondheim = DirectoryModuleSource(
        enabling_statement={'name': 'trondheim::*', 'trusted': False},
        modules_directory=modules_directory_path,
    )

    assert len(tuple(modules_config.external_module_sources)) == 2

    assert oslo in tuple(modules_config.external_module_sources)
    assert trondheim in tuple(modules_config.external_module_sources)

    # Test that all module config files are correctly set
    assert oslo_path / 'config.yml' in modules_config.external_module_config_files
    assert trondheim_path / 'config.yml' in modules_config.external_module_config_files

def test_external_module(test_config_directory):
    modules_directory_path = test_config_directory / 'test_modules'
    oslo = DirectoryModuleSource(
        enabling_statement={'name': 'oslo::*'},
        modules_directory=modules_directory_path,
    )

    oslo_path = test_config_directory / 'test_modules' / 'oslo'
    assert oslo.directory == oslo_path
    assert oslo.trusted == True
    assert oslo.relative_directory_path == Path('oslo')
    assert oslo.config_file == oslo_path / 'config.yml'


def test_retrieval_of_external_module_config(test_config_directory):
    external_module_source_config = {'name': 'burma::*'}
    external_module_source = DirectoryModuleSource(
        enabling_statement=external_module_source_config,
        modules_directory=test_config_directory / 'test_modules',
    )

    assert external_module_source.config({}) == {
        f'module/burma::burma': {
            'enabled': True,
            'safe': False,
        },
    }


class TestModuleSource:

    def test_finding_correct_module_source_type_from_name(self):
        assert ModuleSource.type(of='name') == GlobalModuleSource
        assert ModuleSource.type(of='category::name') == DirectoryModuleSource
        assert ModuleSource.type(of='github::user/repo') == GithubModuleSource
        assert ModuleSource.type(of='github::user/repo::module') == GithubModuleSource
        assert ModuleSource.type(of='github::user/repo::*') == GithubModuleSource

    def test_detection_of_all_module_directories_within_a_directory(
        self,
        test_config_directory,
    ):
        assert tuple(EnabledModules.module_directories(
            within=test_config_directory / 'freezed_modules',
        )) == (
            'north_america',
            'south_america',
        )


class TestDirectoryModuleSource:
    """Test of object responsible for module(s) defined in a directory."""

    def test_which_enabling_statements_represents_directory_module_sources(self):
        assert DirectoryModuleSource.represented_by(
            module_name='category::name',
        )
        assert DirectoryModuleSource.represented_by(
            module_name='category/recursive::name',
        )
        assert DirectoryModuleSource.represented_by(
            module_name='category::*',
        )
        assert DirectoryModuleSource.represented_by(
            module_name='*::*',
        )

        assert not DirectoryModuleSource.represented_by(
            module_name='category::*not_valid',
        )
        assert not DirectoryModuleSource.represented_by(
            module_name='category::not_valid*',
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
        enabling_statement = {'name': 'north_america::colombia'}
        with pytest.raises(NonExistentEnabledModule):
            directory_module = DirectoryModuleSource(
                enabling_statement=enabling_statement,
                modules_directory=test_config_directory / 'freezed_modules',
            )
            config = directory_module.config({})

    def test_recursive_module_directory(
        self,
        test_config_directory,
    ):
        enabling_statement = {'name': 'recursive/directory::bulgaria'}
        directory_module = DirectoryModuleSource(
            enabling_statement=enabling_statement,
            modules_directory=test_config_directory / 'test_modules',
        )
        assert directory_module.config({}) == {
            'module/recursive/directory::bulgaria': {
                'on_startup': {
                    'run': "echo 'Greetings from Bulgaria!'",
                },
            },
        }

    def test_getting_config_dict_from_directory_module(
        self,
        test_config_directory,
    ):
        enabling_statement = {'name': 'north_america::USA'}
        directory_module = DirectoryModuleSource(
            enabling_statement=enabling_statement,
            modules_directory=test_config_directory / 'freezed_modules',
        )
        assert directory_module.config({}) == {
            'module/north_america::USA': {
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
        enabling_statement = {'name': 'south_america::brazil'}
        directory_module = DirectoryModuleSource(
            enabling_statement=enabling_statement,
            modules_directory=test_config_directory / 'freezed_modules',
        )
        assert directory_module.config({}) == {
            'module/south_america::brazil': {
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
        enabling_statement = {'name': 'south_america::brazil'}
        directory_module = DirectoryModuleSource(
            enabling_statement=enabling_statement,
            modules_directory=test_config_directory / 'freezed_modules',
        )
        directory_module.config({})

        assert 'south_america::brazil' in directory_module

        assert 'south_america::argentina' not in directory_module
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
            module_name='category::name',
        )
        assert not GlobalModuleSource.represented_by(
            module_name='category::*',
        )
        assert not GlobalModuleSource.represented_by(
            module_name='*::*',
        )
        assert not GlobalModuleSource.represented_by(
            module_name='jakobgm/module',
        )

    def test_that_enabled_modules_are_detected_correctly(self):
        global_module_source = GlobalModuleSource(
            enabling_statement={'name': 'enabled_module'},
            modules_directory=Path('/'),
        )
        global_module_source.config({})
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

        assert 'directory::module' not in global_module_source
        assert 'user/repo' not in global_module_source


class TestGithubModuleSource:

    def test_valid_names_which_indicate_github_modules(self):
        assert GithubModuleSource.represented_by(
            module_name='github::jakobgm/astrality',
        )
        assert GithubModuleSource.represented_by(
            module_name='github::jakobgm/astrality::module',
        )
        assert GithubModuleSource.represented_by(
            module_name='github::jakobgm/astrality::*',
        )
        assert GithubModuleSource.represented_by(
            module_name='github::user_name./repo-git.ast',
        )

        assert not GithubModuleSource.represented_by(
            module_name='w*',
        )
        assert not GithubModuleSource.represented_by(
            module_name='category::name',
        )
        assert not GithubModuleSource.represented_by(
            module_name='category::*',
        )
        assert not GithubModuleSource.represented_by(
            module_name='*::*',
        )
        assert not GithubModuleSource.represented_by(
            module_name='*',
        )
        assert not GithubModuleSource.represented_by(
            module_name='global_module',
        )

    def test_that_username_and_repo_is_identified(self, tmpdir, delete_jakobgm):
        modules_directory = Path(tmpdir)
        github_module_source = GithubModuleSource(
            enabling_statement={'name': 'github::jakobgm/astrality'},
            modules_directory=modules_directory,
        )
        assert github_module_source.github_user == 'jakobgm'
        assert github_module_source.github_repo == 'astrality'

    @pytest.mark.slow
    def test_that_enabled_repos_are_found(self, test_config_directory, delete_jakobgm):
        github_module_source = GithubModuleSource(
            enabling_statement={'name': 'github::jakobgm/test-module.astrality'},
            modules_directory=test_config_directory / 'test_modules',
        )
        github_module_source.config({})

        assert 'github::jakobgm/test-module.astrality::botswana' in github_module_source
        assert 'github::jakobgm/test-module.astrality::ghana' in github_module_source

        assert 'github::jakobgm/test-module.astrality::non_existent' not in github_module_source
        assert 'github::jakobgm/another_repo::ghana' not in github_module_source
        assert 'astrality' not in github_module_source
        assert 'jakobgm' not in github_module_source

    @pytest.mark.slow
    def test_specific_github_modules_enabled(self, test_config_directory, delete_jakobgm):
        github_module_source = GithubModuleSource(
            enabling_statement={'name': 'github::jakobgm/test-module.astrality::botswana'},
            modules_directory=test_config_directory / 'test_modules',
        )
        github_module_source.config({})

        assert 'github::jakobgm/test-module.astrality::botswana' in github_module_source
        assert 'github::jakobgm/test-module.astrality::ghana' not in github_module_source

    @pytest.mark.slow
    def test_that_all_modules_enabled_syntaxes_behave_identically(
        self,
        test_config_directory,
        delete_jakobgm,
    ):
        github_module_source1 = GithubModuleSource(
            enabling_statement={'name': 'github::jakobgm/test-module.astrality'},
            modules_directory=test_config_directory / 'test_modules',
        )
        github_module_source1.config({})

        # Sleep to prevent race conditions
        time.sleep(1)

        github_module_source2 = GithubModuleSource(
            enabling_statement={'name': 'github::jakobgm/test-module.astrality::*'},
            modules_directory=test_config_directory / 'test_modules',
        )
        github_module_source2.config({})

        assert github_module_source1 == github_module_source2

    @pytest.mark.slow
    def test_automatical_retrival_of_github_module(self, tmpdir):
        modules_directory = Path(tmpdir)
        github_module_source = GithubModuleSource(
            enabling_statement={
                'name': 'github::jakobgm/test-module.astrality::*',
                'autoupdate': True,
            },
            modules_directory=modules_directory,
        )
        assert github_module_source.config({}) == {
            'module/github::jakobgm/test-module.astrality::botswana': {
                'on_startup': {
                    'run': "echo 'Greetings from Botswana!'",
                },
            },
            'module/github::jakobgm/test-module.astrality::ghana': {
                'on_startup': {
                    'run': "echo 'Greetings from Ghana!'",
                },
            },
            'context/geography': {
                'botswana': {
                    'capitol': 'Gaborone',
                },
                'ghana': {
                    'capitol': 'Accra',
                },
            },
        }

    @pytest.mark.slow
    def test_use_of_autoupdating_github_source(self, tmpdir):
        modules_directory = Path(tmpdir)

        github_module_source = GithubModuleSource(
            enabling_statement={
                'name': 'github::jakobgm/test-module.astrality',
                'autoupdate': True,
            },
            modules_directory=modules_directory,
        )

        # The repository is lazely cloned, so we need to get the config
        config = github_module_source.config({})

        repo_dir = modules_directory / 'jakobgm' / 'test-module.astrality'
        assert repo_dir.is_dir()

        # Move master to first commit in repository
        result = run_shell(
            command='git reset --hard d4c9723',
            timeout=5,
            fallback=False,
            working_directory=repo_dir,
        )
        assert result is not False

        # The readme does not exist in this commit
        readme = repo_dir / 'README.rst'
        assert not readme.is_file()

        del github_module_source
        github_module_source = GithubModuleSource(
            enabling_statement={
                'name': 'github::jakobgm/test-module.astrality',
                'autoupdate': True,
            },
            modules_directory=modules_directory,
        )
        config = github_module_source.config({})

        # The autoupdating should update the module to origin/master
        # containing the README.rst file
        assert readme.is_file()


class TestEnabledModules:

    def test_processing_of_enabled_statements(
        self,
        test_config_directory,
    ):
        enabled_modules = EnabledModules([], Path('/'), Path('/'))

        assert enabled_modules.process_enabling_statements(
            enabling_statements=[
                {'name': '*::*'}
            ],
            modules_directory=test_config_directory / 'freezed_modules',
        ) == [{'name': 'north_america::*'}, {'name': 'south_america::*'}]
        assert enabled_modules.all_directory_modules_enabled == True
        assert enabled_modules.all_global_modules_enabled == False


    @pytest.mark.slow
    def test_enabled_detection(
        self,
        test_config_directory,
        caplog,
        delete_jakobgm,
    ):
        enabling_statements = [
            {'name': 'global'},
            {'name': 'south_america::*'},
            {'name': 'github::jakobgm/test-module.astrality'},
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

        enabled_modules.compile_config_files({})
        assert 'global' in enabled_modules
        assert 'south_america::brazil' in enabled_modules
        assert 'south_america::argentina' in enabled_modules
        assert 'github::jakobgm/test-module.astrality::botswana' in enabled_modules
        assert 'github::jakobgm/test-module.astrality::ghana' in enabled_modules

        assert 'not_enabled' not in enabled_modules
        assert 'non_existing_folder::non_existing_module' not in enabled_modules
        assert 'github::user/not_enabled' not in enabled_modules

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

        assert 'south_america::brazil' not in enabled_modules
        assert 'south_america::argentina' not in enabled_modules
        assert 'github::jakobgm/color_schemes.astrality' not in enabled_modules
