"""Test module for enabled modules sourced from Github."""
from pathlib import Path

import pytest

from astrality.exceptions import GithubModuleError
from astrality.github import clone_repo


def test_clone_github_repo(tmpdir):
    modules_directory = Path(tmpdir.mkdir('modules'))
    repo_dir = clone_repo(
        user='jakobgm',
        repository='color-schemes.astrality',
        modules_directory=modules_directory,
    )
    assert repo_dir.is_dir()

    module_config = repo_dir / 'config.yml'
    assert module_config.is_file()

    assert repo_dir.name == 'color-schemes.astrality'
    assert repo_dir.parent.name == 'jakobgm'


def test_cloning_non_existent_github_repository(tmpdir):
    modules_directory = Path(tmpdir.mkdir('modules'))

    with pytest.raises(GithubModuleError):
        clone_repo(
            user='jakobgm',
            repository='i-will-never-create-this-repository',
            modules_directory=modules_directory,
        )

    github_user_directory = modules_directory / 'jakobgm'
    assert not github_user_directory.is_dir()

    repository_directory = github_user_directory / 'i-will-never-create-this-repository'
    assert not repository_directory.is_dir()


def test_cloning_two_repositories(tmpdir):
    modules_directory = Path(tmpdir.mkdir('modules'))
    repo_dir = clone_repo(
        user='jakobgm',
        repository='color-schemes.astrality',
        modules_directory=modules_directory,
    )
    repo_dir = clone_repo(
        user='jakobgm',
        repository='solar-desktop.astrality',
        modules_directory=modules_directory,
    )

    github_user_directory = modules_directory / 'jakobgm'
    assert len(tuple(github_user_directory.iterdir())) == 2


def test_cloning_one_existent_and_one_non_existent_repo(tmpdir):
    modules_directory = Path(tmpdir.mkdir('modules'))
    repo_dir = clone_repo(
        user='jakobgm',
        repository='color-schemes.astrality',
        modules_directory=modules_directory,
    )

    with pytest.raises(GithubModuleError):
        repo_dir = clone_repo(
            user='jakobgm',
            repository='i-will-never-create-this-repository',
            modules_directory=modules_directory,
        )

    github_user_directory = modules_directory / 'jakobgm'
    assert len(tuple(github_user_directory.iterdir())) == 1


def test_cloning_the_same_repo_twice(tmpdir):
    modules_directory = Path(tmpdir.mkdir('modules'))
    repo_dir = clone_repo(
        user='jakobgm',
        repository='color-schemes.astrality',
        modules_directory=modules_directory,
    )

    config_file = modules_directory / 'jakobgm' / 'color-schemes.astrality' / 'config.yml'
    config_file.write_text('user edited')

    repo_dir = clone_repo(
        user='jakobgm',
        repository='color-schemes.astrality',
        modules_directory=modules_directory,
    )

    with open(config_file) as file:
        assert file.read() == 'user edited'
