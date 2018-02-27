import logging
import os
from pathlib import Path
from typing import Union

from astrality.exceptions import GithubModuleError
from astrality.utils import run_shell

def clone_repo(
    user: str,
    repository: str,
    modules_directory: Path,
    timeout: Union[int, float] = 50,
) -> Path:
    """
    Clone Github `user`/`repository` to modules_directory.

    The resulting repository is placed in:
    <modules_directory>/<user>/<repository>.
    """

    github_user_directory = modules_directory / user
    github_user_directory.mkdir(parents=True, exist_ok=True)
    repository_directory = github_user_directory / repository
    github_url = f'https://github.com/{user}/{repository}.git {repository_directory}'

    # Fail on git credential prompt: https://serverfault.com/a/665959
    result = run_shell(
        command='GIT_TERMINAL_PROMPT=0 git clone ' + github_url,
        timeout=timeout,
        fallback=False,
        working_directory=github_user_directory,
        allow_error_codes=True,
    )

    if not repository_directory.is_dir() or result is False:
        try:
            github_user_directory.rmdir()
        except OSError:
            pass

        raise GithubModuleError(
            f'Could not clone repository "{user}/{repository}.\n'
            f'Return value from cloning operation: "{result}".'
        )

    return repository_directory


def clone_or_pull_repo(
    user: str,
    repository: str,
    modules_directory: Path,
    timeout: Union[int, float] = 50,
) -> Path:
    github_repo_directory = modules_directory / user / repository

    if not github_repo_directory.is_dir():
        # The repository does not exist, so we clone it
        return clone_repo(
            user=user,
            repository=repository,
            modules_directory=modules_directory,
            timeout=timeout,
        )

    logger = logging.getLogger(__name__)
    if not (github_repo_directory / '.git').is_dir():
        logger.error(
            f'Tried to update git module directory "{github_repo_directory}", '
            'but the directory does not contain a ".git" sub-directory.'
        )
        return github_repo_directory

    result = run_shell(
        command='GIT_TERMINAL_PROMPT=0 git pull',
        timeout=timeout,
        fallback=False,
        working_directory=github_repo_directory,
        allow_error_codes=True,
    )
    if result is False:
        raise GithubModuleError(
            f'Could not git pull module directory "{github_repo_directory}".\.'
            f'Return value from git pull operation: "{result}".'
        )

    return github_repo_directory
