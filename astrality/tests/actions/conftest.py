"""Test configuration for the astrality.actions module."""

from pathlib import Path

import pytest

from astrality.config import GlobalModulesConfig


@pytest.fixture
def global_modules_config():
    return GlobalModulesConfig(
        config={},
        config_directory=Path(__file__).parent,
    )
