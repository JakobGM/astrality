"""Application wide fixtures."""
import os
from pathlib import Path
import shutil

import pytest

import astrality
from astrality.actions import ActionBlock
from astrality.config import GlobalModulesConfig, user_configuration
from astrality.context import Context
from astrality.module import Module, ModuleManager


@pytest.fixture
def conf_path():
    """Return str path to configuration directory."""
    conf_path = Path(__file__).parents[1] / 'config'
    return conf_path


@pytest.fixture
def conf_file_path(conf_path):
    """Return path to example configuration."""
    return conf_path / 'astrality.yml'


@pytest.fixture(scope='session', autouse=True)
def conf():
    """Return the configuration object for the example configuration."""
    this_test_file = os.path.abspath(__file__)
    conf_path = Path(this_test_file).parents[1] / 'config'
    return user_configuration(conf_path)[0]


@pytest.fixture(scope='session', autouse=True)
def context():
    """Return the context object for the example configuration."""
    this_test_file = os.path.abspath(__file__)
    conf_path = Path(this_test_file).parents[1] / 'config'
    return user_configuration(conf_path)[2]


@pytest.fixture(scope='session', autouse=True)
def modules():
    """Return the modules object for the example configuration."""
    this_test_file = os.path.abspath(__file__)
    conf_path = Path(this_test_file).parents[1] / 'config'
    return user_configuration(conf_path)[1]


@pytest.fixture
def test_config_directory():
    """Return path to test config directory."""
    return Path(__file__).parent / 'test_config'


@pytest.yield_fixture
def temp_directory(tmpdir):
    """Return path to temporary directory, and cleanup afterwards."""
    return Path(tmpdir).resolve()


@pytest.fixture
def context_directory(test_config_directory):
    """Return path to directory containing several context files."""
    return test_config_directory / 'context'


@pytest.fixture
def template_directory(test_config_directory):
    """Return path to directory containing several templates"""
    return test_config_directory / 'templates'


@pytest.fixture
def module_factory(test_config_directory):
    """Return Module factory for testing."""
    def _module_factory(
        name='test',
        on_startup=None,
        on_modified=None,
        on_exit=None,
        path=None,
        module_directory=test_config_directory / 'test_modules' /
        'using_all_actions',
        replacer=lambda x: x,
        context_store={},
    ) -> Module:
        """Return module with specified action blocks and config."""
        module = Module(
            name=name,
            module_config={},
            module_directory=module_directory,
            replacer=replacer,
            context_store=context_store,
        )
        if on_startup:
            module.action_blocks['on_startup'] = on_startup

        if on_exit:
            module.action_blocks['on_exit'] = on_exit

        if on_modified:
            module.action_blocks['on_modified'][path] = on_modified

        return module

    return _module_factory


@pytest.fixture
def module_manager_factory():
    """Return ModuleManager factory for testing."""
    def _module_manager_factory(
        *modules,
        context=Context(),
    ) -> ModuleManager:
        """Return ModuleManager object with given modules and context."""
        module_manager = ModuleManager(
            context=context,
        )
        module_manager.modules = {
            module.name: module
            for module
            in modules
        }

        # Insert correct context for all actions
        for module in modules:
            for block in module.all_action_blocks():
                for action_type in ActionBlock.action_types:
                    for actions in getattr(block, f'_{action_type}_actions'):
                        actions.context_store = context

        return module_manager

    return _module_manager_factory


@pytest.fixture
def create_temp_files(tmpdir):
    """Return temp file factory function."""
    temp_dir = Path(tmpdir)

    def _create_temp_files(number):
        """Create `number` tempfiles in seperate directories and yield paths."""
        for _number in range(number):
            temp_file = temp_dir / str(_number) / f'file{_number}.temp'
            temp_file.parent.mkdir(parents=True)
            temp_file.touch()
            yield temp_file

    return _create_temp_files


@pytest.fixture
def action_block_factory(test_config_directory):
    """Return action block factory function for testing."""

    def _action_block_factory(
        import_context={},
        compile={},
        copy={},
        run={},
        stow={},
        symlink={},
        directory=test_config_directory,
        replacer=lambda x: x,
        context_store=Context(),
    ):
        """Return module with given parameters."""
        config = {
            'import_context': import_context,
            'compile': compile,
            'copy': copy,
            'run': run,
            'stow': stow,
            'symlink': symlink,
        }

        return ActionBlock(
            action_block=config,
            directory=directory,
            replacer=replacer,
            context_store=context_store,
            global_modules_config=GlobalModulesConfig(
                config={},
                config_directory=test_config_directory,
            ),
            module_name='test',
        )

    return _action_block_factory


@pytest.yield_fixture(autouse=True)
def patch_xdg_directory_standard(tmpdir, monkeypatch, request):
    """During testing, the XDG directory standard is monkeypatched."""
    if 'dont_patch_xdg' in request.keywords:
        yield
        return

    data_dir = Path(tmpdir).parent / '.local' / 'share' / 'astrality'

    # Clear data directory before the test
    if data_dir.exists():
        shutil.rmtree(str(data_dir))
    data_dir.mkdir(parents=True)

    monkeypatch.setattr(
        astrality.xdg.XDG,
        'data_home',
        data_dir,
    )

    yield data_dir

    # Delete directory for next test
    if data_dir.exists():
        shutil.rmtree(str(data_dir))


@pytest.fixture(autouse=True)
def patch_astrality_config_home(monkeypatch):
    """Patch $ASTRALITY_CONFIG_HOME."""
    example_config = Path(__file__).parents[2] / 'config'
    monkeypatch.setitem(
        os.environ,
        'ASTRALITY_CONFIG_HOME',
        str(example_config),
    )
