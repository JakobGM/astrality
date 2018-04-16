"""Tests for string interpolations in ModuleManager class."""

from pathlib import Path
import logging

from astrality.module import ModuleManager

def test_use_of_string_interpolations_of_module(
    default_global_options,
    _runtime,
    tmpdir,
    caplog,
    template_directory,
):
    """Path placeholders should be replaced with compilation target."""
    temp_dir = Path(tmpdir)

    a_template = temp_dir / 'a.template'
    a_template.write_text('foobar')

    b_template = temp_dir / 'b.template'
    b_template.write_text('')
    b_target = temp_dir / 'b.target'
    b_on_modified = template_directory / 'empty.template'

    c_template = temp_dir / 'c.template'
    c_template.write_text('')
    c_target = temp_dir / 'c.target'

    application_config = {
        'module/A': {
            'on_startup': {
                'compile': [
                    {'source': str(a_template)}
                ],
            },
        },
        'module/B': {
            'on_modified': {
                str(b_on_modified): {
                    'compile': [
                        {
                            'source': str(b_template),
                            'target': str(b_target),
                        },
                    ],
                },
            }
        },
        'module/C': {
            'on_exit': {
                'compile': {
                        'source': str(c_template),
                        'target': str(c_target),
                },
            },
        },
    }

    application_config.update(default_global_options)
    _runtime['_runtime']['config_directory'] = temp_dir
    application_config.update(_runtime)
    module_manager = ModuleManager(application_config)

    # Compile twice to double check that only one temporary file is inserted
    module_manager.modules['A'].compile('on_startup')
    module_manager.modules['A'].compile('on_startup')
    a_target = list(
        module_manager.modules['A'].performed_compilations().values(),
    )[0].pop()

    # Temporary compilation targets should be inserted
    assert module_manager.modules['A'].interpolate_string(
        'one two {' + str(a_template) + '}',
    ) == 'one two ' + str(a_target)

    assert module_manager.modules['A'].interpolate_string(
        '{leave/me/alone}'
    ) == '{leave/me/alone}'


    # Specified compilation targets should be inserted
    module_manager.modules['B'].compile('on_modified', b_on_modified)
    assert module_manager.modules['B'].interpolate_string(
        '{' + str(b_template) + '}',
    ) == str(b_target)

    # Relative paths should be resolved
    module_manager.modules['C'].compile('on_exit')
    assert module_manager.modules['C'].interpolate_string(
        '{c.template/into/..}',
    ) == str(c_target)

    # Check that incorrect placeholders are logged
    caplog.clear()
    module_manager.modules['C'].interpolate_string(
        '{/not/here}',
    )
    assert caplog.record_tuples == [(
        'astrality',
        logging.ERROR,
        'String placeholder {/not/here} could not be replaced. '
        '"/not/here" has not been compiled.',
    )]
