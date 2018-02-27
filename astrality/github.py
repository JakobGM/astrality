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

