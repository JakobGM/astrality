"""Tests for astrality.config.expand_path."""

from pathlib import Path

from astrality.config import expand_globbed_path, expand_path


def test_expand_path_method(test_config_directory):
    absolute_path = Path('/dir/ast')
    tilde_path = Path('~/dir')
    relative_path = Path('test')

    assert expand_path(
        path=absolute_path,
        config_directory=Path('/what/ever'),
    ) == absolute_path

    assert expand_path(
        path=tilde_path,
        config_directory=Path('/what/ever'),
    ) == Path.home() / 'dir'

    assert expand_path(
        path=relative_path,
        config_directory=test_config_directory,
    ) == test_config_directory / 'test'


def test_expansion_of_environment_variables(test_config_directory):
    """
    Environment variables should be expanded in paths.

    See pytest.ini for available environment variables.
    """
    assert expand_path(
        path=Path('${EXAMPLE_ENV_VARIABLE}/recursive'),
        config_directory=test_config_directory / '$EXAMPLE_ENV_VARIABLE',
    ) == test_config_directory / 'test_value' / 'test_value' / 'recursive'


def test_expand_globbed_path(test_config_directory):
    """Globbed paths should allow one level of globbing."""
    templates = Path('test_modules', 'using_all_actions')
    paths = expand_globbed_path(
        path=templates / '*',
        config_directory=test_config_directory,
    )
    assert len(paths) == 5
    assert test_config_directory / templates / 'module.template' in paths


def test_expand_recursive_globbed_path(test_config_directory):
    """Globbed paths should allow recursive globbing."""
    templates = Path('test_modules', 'using_all_actions')
    paths = expand_globbed_path(
        path=templates / '**' / '*',
        config_directory=test_config_directory,
    )
    assert len(paths) == 6
    assert test_config_directory / templates / 'recursive' / 'empty.template' \
        in paths
