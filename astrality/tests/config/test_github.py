"""Test module for enabled modules sourced from Github."""
from pathlib import Path

import pytest

from astrality.exceptions import GithubModuleError
from astrality.github import clone_or_pull_repo, clone_repo
from astrality.utils import run_shell


@pytest.mark.slow
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


@pytest.mark.slow
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


@pytest.mark.slow
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


@pytest.mark.slow
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


@pytest.mark.slow
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

@pytest.mark.slow
def test_clone_or_pull_repository_by_updating_outdated_repository(tmpdir):
    modules_directory = Path(tmpdir.mkdir('modules'))
    repo_dir = clone_repo(
        user='jakobgm',
        repository='color-schemes.astrality',
        modules_directory=modules_directory,
    )

    # Move master to first commit in repository
    result = run_shell(
        command='git reset --hard 2b8941a',
        timeout=5,
        fallback=False,
        working_directory=repo_dir,
    )
    assert result is not False

    # The readme does not exist in this commit
    readme = repo_dir / 'README.rst'
    assert not readme.is_file()

    # The following pull should reintroduce the README into the directory
    updated_repo_dir = clone_or_pull_repo(
        user='jakobgm',
        repository='color-schemes.astrality',
        modules_directory=modules_directory,
    )
    assert updated_repo_dir == repo_dir
    assert readme.is_file()
