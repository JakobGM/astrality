"""Application wide test configuration."""
import pytest


def pytest_addoption(parser):
    """Add command line flags to pytest."""
    parser.addoption("--runslow", action="store_true",
                     default=False, help="run slow tests")


def pytest_collection_modifyitems(config, items):
    """Skip slow tests if not --runslow is given to pytest."""
    if config.getoption("--runslow"):
        # --runslow given in cli: do not skip slow tests
        return
    else:  # pragma: no cover
        skip_slow = pytest.mark.skip(reason="need --runslow option to run")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)
