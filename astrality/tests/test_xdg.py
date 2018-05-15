"""Tests for astrality.xdg module."""

import os
from pathlib import Path

import pytest

from astrality.xdg import XDG


@pytest.mark.dont_patch_xdg
def test_xdg_data_home_default_location(monkeypatch):
    """Default location for XDG_DATA_HOME should be respected."""
    xdg = XDG()
    default_dir = xdg.data_home
    assert default_dir == Path('~/.local/share/astrality').expanduser()
    assert default_dir.is_dir()


@pytest.mark.dont_patch_xdg
def test_xdg_data_home_using_environment_variable(monkeypatch, tmpdir):
    """XDG_DATA_HOME environment variables should be respected."""
    custom_data_home = Path(tmpdir, 'data')
    monkeypatch.setattr(
        os,
        'environ',
        {'XDG_DATA_HOME': str(custom_data_home)},
    )

    xdg = XDG()
    data_home = xdg.data_home
    assert data_home == custom_data_home / 'astrality'
    assert data_home.is_dir()


def test_retrieving_data_resource(patch_xdg_directory_standard):
    """The data method should retrieve file resource from data home."""
    xdg = XDG()
    resource = xdg.data('modules/test.tmp')
    assert resource == patch_xdg_directory_standard / 'modules' / 'test.tmp'
    assert resource.exists()

    # We should get the same file again
    resource.write_text('hello')
    refetched_resource = xdg.data('modules/test.tmp')
    assert refetched_resource.read_text() == 'hello'
