from pathlib import Path

import pytest

from astrality.module import ModuleManager


@pytest.mark.parametrize("specified_permission,expected_permission", [
        ("777", 0o777),
        ("100", 0o100),
])
def test_compiling_template_with_specific_permissions(
    default_global_options,
    _runtime,
    test_config_directory,
    tmpdir,
    specified_permission,
    expected_permission,
):
    template = test_config_directory / 'templates' / 'empty.template'
    target = Path(tmpdir) / 'target'

    application_config = {
        'module/test': {
            'on_startup': {
                'compile': {
                    'content': str(template),
                    'target': str(target),
                    'permissions': specified_permission,
                },
            },
        },
    }
    application_config.update(default_global_options)
    application_config.update(_runtime)

    module_manager = ModuleManager(application_config)
    module_manager.finish_tasks()

    assert (target.stat().st_mode & 0o777) == expected_permission
