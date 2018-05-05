from pathlib import Path

import pytest

from astrality.module import ModuleManager


@pytest.mark.parametrize('specified_permission,expected_permission', [
    ('777', 0o777),
    ('100', 0o100),
])
def test_compiling_template_with_specific_permissions(
    test_config_directory,
    tmpdir,
    specified_permission,
    expected_permission,
):
    template = test_config_directory / 'templates' / 'empty.template'
    target = Path(tmpdir) / 'target'

    modules = {
        'test': {
            'on_startup': {
                'compile': {
                    'content': str(template),
                    'target': str(target),
                    'permissions': specified_permission,
                },
            },
        },
    }

    module_manager = ModuleManager(
        modules=modules,
    )
    module_manager.finish_tasks()

    assert (target.stat().st_mode & 0o777) == expected_permission
