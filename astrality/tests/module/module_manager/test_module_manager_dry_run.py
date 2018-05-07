"""Tests for finishing ModuleManager tasks with dry_run set to True."""

from astrality.module import ModuleManager


def test_that_dry_run_is_respected(create_temp_files):
    """ModuleManager should pass on dry_run to its actions."""
    (
        touched,
        copy_content,
        copy_target,
        compile_content,
        compile_target,
        symlink_content,
        symlink_target,
    ) = create_temp_files(7)
    touched.unlink()
    copy_target.write_text('copy_original')
    compile_target.write_text('compile_original')

    modules = {
        'A': {
            'run': {
                'shell': 'touch ' + str(touched),
            },
            'copy': {
                'content': str(copy_content),
                'target': str(copy_target),
            },
            'compile': {
                'content': str(compile_content), 'target': str(compile_target),
            },
            'symlink': {
                'content': str(symlink_content), 'target': str(symlink_target),
            },
        },
    }
    module_manager = ModuleManager(
        modules=modules,
        directory=touched.parents[1],
        dry_run=True,
    )
    module_manager.finish_tasks()

    assert not touched.exists()
    assert copy_target.read_text() == 'copy_original'
    assert compile_target.read_text() == 'compile_original'
    assert not symlink_target.is_symlink()
