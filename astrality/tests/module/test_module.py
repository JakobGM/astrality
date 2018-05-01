"""Tests for Module class."""

import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path

from freezegun import freeze_time
import pytest

from astrality import event_listener
from astrality.module import Module, ModuleManager
from astrality.context import Context
from astrality.tests.utils import RegexCompare
from astrality.utils import generate_expanded_env_dict


@pytest.fixture
def valid_module_section():
    return {
        'module/test_module': {
            'enabled': True,
            'event_listener': {'type': 'weekday'},
            'on_startup': {
                'run': [{'shell': 'echo {event}'}],
                'compile': [
                    {
                        'content': '../templates/test_template.conf',
                        'target': '/tmp/compiled_result',
                    },
                ],
            },
            'on_event': {
                'run': [{'shell': 'echo {../templates/test_template.conf}'}],
            },
            'on_exit': {
                'run': [{'shell': 'echo exit'}],
            },
        }
    }


@pytest.fixture
def simple_application_config(
    valid_module_section,
    expanded_env_dict,
    default_global_options,
    _runtime,
):
    config = valid_module_section.copy()
    config.update(default_global_options)
    config.update(_runtime)

    config['context/env'] = expanded_env_dict
    config['context/fonts'] = {1: 'FuraMono Nerd Font'}

    # Increase run timeout, so that we can inspect the shell results
    config['config/modules'] = {'run_timeout': 2}
    return config


@pytest.fixture
def module(
    valid_module_section,
    test_config_directory,
):
    return Module(
        module_config=valid_module_section,
        module_directory=test_config_directory,
    )


@pytest.fixture
def single_module_manager(simple_application_config):
    return ModuleManager(simple_application_config)


class TestModuleClass:

    def test_valid_class_section_method_with_valid_section(
        self,
        valid_module_section,
    ):
        assert Module.valid_class_section(
            section=valid_module_section,
            requires_timeout=2,
            requires_working_directory=Path('/'),
        ) is True

    def test_valid_class_section_method_with_disabled_module_section(self):
        disabled_module_section = {
            'module/disabled_test_module': {
                'enabled': False,
                'on_startup': {'run': ['test']},
                'on_event': {'run': ['']},
                'on_exit': {'run': ['whatever']},
            }
        }
        assert Module.valid_class_section(
            section=disabled_module_section,
            requires_timeout=2,
            requires_working_directory=Path('/'),
        ) is False

    def test_valid_class_section_method_with_invalid_section(self):
        invalid_module_section = {
            'context/fonts': {
                'some_key': 'some_value',
            }
        }
        assert Module.valid_class_section(
            section=invalid_module_section,
            requires_timeout=2,
            requires_working_directory=Path('/'),
        ) is False

    def test_valid_class_section_with_wrongly_sized_dict(
        self,
        valid_module_section,
    ):
        invalid_module_section = valid_module_section
        invalid_module_section.update({'module/valid2': {'enabled': True}})

        with pytest.raises(RuntimeError):
            Module.valid_class_section(
                section=invalid_module_section,
                requires_timeout=2,
                requires_working_directory=Path('/'),
            )

    def test_module_name(self, module):
        assert module.name == 'test_module'

    def test_module_event_listener_class(self, module):
        assert isinstance(module.event_listener, event_listener.Weekday)

    def test_using_default_static_event_listener_when_no_event_listener_given(
        self,
        test_config_directory
    ):
        static_module = Module(
            module_config={'module/static': {}},
            module_directory=test_config_directory,
        )
        assert isinstance(static_module.event_listener, event_listener.Static)

    @freeze_time('2018-01-27')
    def test_running_module_manager_commands_with_special_interpolations(
        self,
        single_module_manager,
        caplog,
    ):
        single_module_manager.startup()
        assert (
            'astrality.actions',
            logging.INFO,
            'Running command "echo saturday".',
        ) in caplog.record_tuples
        assert (
            'astrality',
            logging.INFO,
            'saturday\n',
        ) in caplog.record_tuples

        caplog.clear()
        single_module_manager.execute(
            action='run',
            block='on_event',
            module=single_module_manager.modules['test_module'],
        )
        assert (
            'astrality.actions',
            logging.INFO,
            'Running command "echo /tmp/compiled_result".',
        ) in caplog.record_tuples

    @freeze_time('2018-01-27')
    def test_running_module_startup_command(
        self,
        single_module_manager,
        module,
        valid_module_section,
        caplog,
    ):
        single_module_manager.startup()

        assert caplog.record_tuples == [
            (
                'astrality',
                logging.INFO,
                RegexCompare(
                    r'\[Compiling\].+test_template\.conf.+compiled_result"',
                ),
            ),
            (
                'astrality.actions',
                logging.INFO,
                'Running command "echo saturday".',
            ),
            (
                'astrality',
                logging.INFO,
                'saturday\n',
            )
        ]

    def test_running_module_on_event_command(
        self,
        single_module_manager,
        module,
        caplog,
    ):
        single_module_manager.startup()
        caplog.clear()

        single_module_manager.execute(
            action='run',
            block='on_event',
            module=single_module_manager.modules['test_module'],
        )

        # Convoluted way of getting the compilation target. Sorry!
        compiled_template = list(
            single_module_manager
            .modules['test_module']
            .performed_compilations()
            .values(),
        )[0].pop()

        assert caplog.record_tuples == [
            (
                'astrality.actions',
                logging.INFO,
                f'Running command "echo {compiled_template}".',
            ),
            (
                'astrality',
                logging.INFO,
                f'{compiled_template}\n',
            )
        ]

    def test_running_module_exit_command(self, single_module_manager, caplog):
        single_module_manager.exit()
        assert caplog.record_tuples == [
            (
                'astrality.actions',
                logging.INFO,
                'Running command "echo exit".',
            ),
            (
                'astrality',
                logging.INFO,
                'exit\n',
            )
        ]

    def test_missing_template_file(
        self,
        default_global_options,
        _runtime,
        caplog,
    ):
        application_config = {
            'module/test_module': {
                'on_startup': {
                    'compile': [
                        {'content': '/not/existing'},
                    ],
                },
            },
        }

        application_config.update(default_global_options)
        application_config.update(_runtime)

        module_manager = ModuleManager(application_config)

        caplog.clear()
        module_manager.finish_tasks()
        assert 'Could not compile template "/not/existing" '\
               'to target "' in caplog.record_tuples[0][2]

    def test_compilation_of_template(
        self,
        simple_application_config,
        module,
        conf,
        caplog,
    ):
        simple_application_config[
            'module/test_module'
        ][
            'event_listener'
        ][
            'type'
        ] = 'solar'

        compiled_template_content = 'some text\n' + os.environ['USER'] \
            + '\nFuraMono Nerd Font'
        module_manager = ModuleManager(simple_application_config)
        directory = module_manager.config_directory

        caplog.clear()
        module_manager.execute(action='compile', block='on_startup')

        template_file = str(
            (directory / '../templates/test_template.conf').resolve()
        )
        compiled_template = str(
            list(
                module_manager.modules['test_module']
                .performed_compilations()[Path(template_file)]
            )[0]
        )

        with open('/tmp/compiled_result', 'r') as file:
            compiled_result = file.read()

        assert compiled_template_content == compiled_result
        assert caplog.record_tuples == [
            (
                'astrality',
                logging.INFO,
                f'[Compiling] Template: "{template_file}" '
                f'-> Target: "{compiled_template}"'
            ),
        ]


def test_running_finished_tasks_command(
    simple_application_config,
    freezer,
    caplog,
):
    """Test that every task is finished at first finish_tasks() invocation."""
    thursday = datetime(
        year=2018,
        month=2,
        day=15,
        hour=12,
    )
    freezer.move_to(thursday)
    module_manager = ModuleManager(simple_application_config)

    caplog.clear()
    module_manager.finish_tasks()

    # Only startup commands should be finished at first
    assert caplog.record_tuples == [
        (
            'astrality',
            logging.INFO,
            RegexCompare(
                r'\[Compiling\] Template: ".+/templates/test_template.conf" '
                r'-> Target: "/tmp/compiled_result"'
            ),
        ),
        (
            'astrality.actions',
            logging.INFO,
            'Running command "echo thursday".',
        ),
        (
            'astrality',
            logging.INFO,
            'thursday\n',
        ),
    ]

    # Now move one day ahead, and observe if event commands are run
    caplog.clear()
    friday = datetime(
        year=2018,
        month=2,
        day=16,
        hour=12,
    )
    freezer.move_to(friday)
    module_manager.finish_tasks()
    assert caplog.record_tuples == [
        (
            'astrality',
            logging.INFO,
            '[module/test_module] New event "friday". '
            'Executing actions.'
        ),
        (
            'astrality.actions',
            logging.INFO,
            'Running command "echo /tmp/compiled_result".',
        ),
        (
            'astrality',
            logging.INFO,
            '/tmp/compiled_result\n',
        ),
    ]


def test_has_unfinished_tasks(simple_application_config, freezer):
    # Move time to midday
    midday = datetime.now().replace(hour=12, minute=0)
    freezer.move_to(midday)

    # At instanziation, the module should have unfinished tasks
    weekday_module = ModuleManager(simple_application_config)
    assert weekday_module.has_unfinished_tasks() is True

    # After finishing tasks, there should be no unfinished tasks (duh!)
    weekday_module.finish_tasks()
    assert weekday_module.has_unfinished_tasks() is False

    # If we move the time forwards, but not to a new event, there should still
    # not be any unfinished tasks
    before_midnight = datetime.now().replace(hour=23, minute=59)
    freezer.move_to(before_midnight)
    assert weekday_module.has_unfinished_tasks() is False

    # But right after a event (new weekday), there should be unfinished
    # tasks
    two_minutes = timedelta(minutes=2)
    freezer.move_to(before_midnight + two_minutes)
    assert weekday_module.has_unfinished_tasks() is True

    # Again, after finishing tasks, there should be no unfinished tasks left
    weekday_module.finish_tasks()
    assert weekday_module.has_unfinished_tasks() is False


@pytest.fixture
def config_with_modules(default_global_options):
    return {
        'config/astrality': default_global_options['config/astrality'],
        'context/env': generate_expanded_env_dict(),
        'module/solar_module': {
            'enabled': True,
            'event_listener': {
                'type': 'solar',
                'longitude': 0,
                'latitude': 0,
                'elevation': 0,
            },
            'templates': {
                'template_name': {
                    'content': 'astrality/tests/templates/test_template.conf',
                    'target': '/tmp/compiled_result',
                }
            },
            'on_startup': {
                'run': [{'shell': 'echo solar compiling {template_name}'}],
            },
            'on_event': {
                'run': [{'shell': 'echo solar {event}'}],
            },
            'on_exit': {
                'run': [{'shell': 'echo solar exit'}],
            },
        },
        'module/weekday_module': {
            'enabled': True,
            'event_listener': {'type': 'weekday'},
            'on_startup': {
                'run': [{'shell': 'echo weekday startup'}],
            },
            'on_event': {
                'run': [{'shell': 'echo weekday {event}'}],
            },
            'on_exit': {
                'run': [{'shell': 'echo weekday exit'}],
            },
        },
        'module/disabled_module': {
            'enabled': False,
            'event_listener': 'static',
        },
        'context/fonts': {1: 'FuraCode Nerd Font'},
        '_runtime': {
            'config_directory': Path(__file__).parents[3],
            'temp_directory': '/tmp',
        }
    }


@pytest.fixture
def module_manager(config_with_modules):
    return ModuleManager(config_with_modules)


def test_import_sections_on_event(config_with_modules, freezer):
    config_with_modules[
        'module/weekday_module'
    ]['on_event']['import_context'] = [{
        'to_section': 'week',
        'from_path': 'astrality/tests/templates/weekday.yml',
        'from_section': '{event}',
    }]

    config_with_modules.pop('module/solar_module')
    module_manager = ModuleManager(config_with_modules)

    assert module_manager.application_context['fonts'] \
        == Context({1: 'FuraCode Nerd Font'})

    sunday = datetime(year=2018, month=2, day=4)
    freezer.move_to(sunday)
    module_manager.finish_tasks()

    # Make application_context comparisons easier
    del module_manager.application_context._dict['env']

    # Startup does not count as a event, so no context has been imported
    assert module_manager.application_context == Context({
        'fonts': Context({1: 'FuraCode Nerd Font'}),
    })

    monday = datetime(year=2018, month=2, day=5)
    freezer.move_to(monday)
    module_manager.finish_tasks()

    # The event has now changed, so context should be imported
    assert module_manager.application_context == {
        'fonts': Context({1: 'FuraCode Nerd Font'}),
        'week': Context({'day': 'monday'}),
    }


def test_import_sections_on_startup(config_with_modules, freezer):
    # Insert day the module was started into 'start day'
    config_with_modules[
        'module/weekday_module'
    ]['on_startup']['import_context'] = [{
        'to_section': 'start_day',
        'from_path': 'astrality/tests/templates/weekday.yml',
        'from_section': '{event}',
    }]

    # Insert the current day into 'day_now'
    config_with_modules[
        'module/weekday_module'
    ]['on_event']['import_context'] = [{
        'to_section': 'day_now',
        'from_path': 'astrality/tests/templates/weekday.yml',
        'from_section': '{event}',
    }]
    config_with_modules.pop('module/solar_module')
    module_manager = ModuleManager(config_with_modules)

    # Remove 'env' context for easier comparisons
    del module_manager.application_context._dict['env']

    # Before finishing tasks, no context sections are imported
    assert module_manager.application_context['fonts'] \
        == {1: 'FuraCode Nerd Font'}

    # Start module on a monday
    sunday = datetime(year=2018, month=2, day=4)
    freezer.move_to(sunday)
    module_manager.finish_tasks()
    assert module_manager.application_context == {
        'fonts': Context({1: 'FuraCode Nerd Font'}),
        'start_day': Context({'day': 'sunday'}),
    }

    # 'now_day' should now be added, but 'start_day' should remain unchanged
    monday = datetime(year=2018, month=2, day=5)
    freezer.move_to(monday)
    module_manager.finish_tasks()
    assert module_manager.application_context == {
        'fonts': Context({1: 'FuraCode Nerd Font'}),
        'start_day': Context({'day': 'sunday'}),
        'day_now': Context({'day': 'monday'}),
    }


class TestModuleManager:
    def test_invocation_of_module_manager_with_config(self, conf):
        ModuleManager(conf)

    @pytest.mark.slow
    def test_using_finish_tasks_on_example_configuration(self, conf):
        module_manager = ModuleManager(conf)
        module_manager.finish_tasks()

    def test_number_of_modules_instanziated_by_module_manager(
        self,
        module_manager,
    ):
        assert len(module_manager) == 2


def test_time_until_next_event_of_several_modules(
    config_with_modules,
    module_manager,
    freezer,
):
    solar_event_listener = event_listener.Solar(config_with_modules)
    noon = solar_event_listener.location.sun()['noon']

    one_minute = timedelta(minutes=1)
    freezer.move_to(noon - one_minute)

    assert module_manager.time_until_next_event() == one_minute
    two_minutes_before_midnight = datetime.now().replace(hour=23, minute=58)
    freezer.move_to(two_minutes_before_midnight)

    assert module_manager.time_until_next_event().total_seconds() \
        == timedelta(minutes=2).total_seconds()


def test_detection_of_new_event_involving_several_modules(
    config_with_modules,
    freezer,
):
    # Move time to right before noon
    solar_event_listener = event_listener.Solar(config_with_modules)
    noon = solar_event_listener.location.sun()['noon']
    one_minute = timedelta(minutes=1)
    freezer.move_to(noon - one_minute)
    module_manager = ModuleManager(config_with_modules)

    # All modules should now considered to have now events
    assert module_manager.has_unfinished_tasks() is True

    # Running on event method for all the event changed modules
    module_manager.finish_tasks()

    # After running these methods, they should all be reverted to not changed
    assert module_manager.has_unfinished_tasks() is False

    # Move time to right after noon
    freezer.move_to(noon + one_minute)

    # The solar event listener should now be considered to have been event
    # changed
    assert module_manager.has_unfinished_tasks() is True

    # Again, check if on_event() method makes them unchanged
    module_manager.finish_tasks()
    assert module_manager.has_unfinished_tasks() is False

    # Move time two days forwards
    two_days = timedelta(days=2)
    freezer.move_to(noon + two_days)

    # Now both event listeners should be considered to have new events
    assert module_manager.has_unfinished_tasks() is True


def test_that_shell_filter_is_run_from_config_directory(
    default_global_options,
    _runtime,
    test_config_directory,
):
    shell_filter_template = Path(__file__).parents[1] \
        / 'templates' / 'shell_filter_working_directory.template'
    shell_filter_template_target = Path(
        '/tmp/astrality/shell_filter_working_directory.template',
    )
    config = {
        'module/A': {
            'on_startup': {
                'compile': [
                    {
                        'content': str(shell_filter_template),
                        'target': str(shell_filter_template_target),
                    }
                ],
            },
        },
    }
    config.update(default_global_options)
    config.update(_runtime)
    module_manager = ModuleManager(config)
    module_manager.execute(action='compile', block='on_startup')

    with open(shell_filter_template_target) as compiled:
        assert compiled.read() == str(test_config_directory)

    os.remove(shell_filter_template_target)


@pytest.yield_fixture
def two_test_file_paths():
    test_file1 = Path('/tmp/astrality/test_file_1')
    test_file2 = Path('/tmp/astrality/test_file_2')

    yield test_file1, test_file2

    # Cleanup files after test has been run (if they exist)
    if test_file1.is_file():
        os.remove(test_file1)
    if test_file2.is_file():
        os.remove(test_file2)


def test_that_only_startup_event_block_is_run_on_startup(
    two_test_file_paths,
    test_config_directory,
    default_global_options,
    _runtime,
    freezer,
):
    thursday = datetime(
        year=2018,
        month=2,
        day=15,
        hour=12,
    )
    freezer.move_to(thursday)

    test_file1, test_file2 = two_test_file_paths
    application_config = {
        'module/A': {
            'event_listener': {'type': 'weekday'},
            'on_startup': {
                'run': [{'shell': 'touch ' + str(test_file1)}],
            },
            'on_event': {
                'run': [{'shell': 'touch ' + str(test_file2)}],
            },
        },
    }
    application_config.update(default_global_options)
    application_config.update(_runtime)
    module_manager = ModuleManager(application_config)

    # Before call to finish_tasks, no actions should have been performed
    assert not test_file1.is_file() and not test_file2.is_file()

    # Now call finish_tasks for the first time, only startup event block should
    # be run
    module_manager.finish_tasks()
    time.sleep(0.5)
    assert test_file1.is_file()
    assert not test_file2.is_file()


def test_trigger_event_module_action(
    test_config_directory,
    default_global_options,
    _runtime,
):
    application_config = {
        'module/A': {
            'event_listener': {'type': 'weekday'},
            'on_startup': {
                'trigger': [
                    {'block': 'on_event'},
                    {'block': 'on_exit'},
                    {'block': 'on_modified', 'path': 'templateA'},
                ],
                'run': [{'shell': 'echo startup'}],
            },
            'on_event': {
                'run': [{'shell': 'echo on_event'}],
                'import_context': [{
                    'from_path': 'context/mercedes.yml',
                    'from_section': 'car',
                }],
            },
            'on_exit': {
                'run': [{'shell': 'echo exit'}],
            },
            'on_modified': {
                'templateA': {
                    'run': [{'shell': 'echo modified.templateA'}],
                    'compile': [
                        {'content': 'templateA'}
                    ],
                },
            },
        },
    }
    application_config.update(default_global_options)
    application_config.update(_runtime)
    module_manager = ModuleManager(application_config)

    # Check that all run commands have been imported into startup block
    results = tuple(module_manager.modules['A'].execute(
        action='run',
        block='on_startup',
    ))
    assert results == (
        ('echo startup', 'startup',),
        ('echo on_event', 'on_event',),
        ('echo exit', 'exit',),
        ('echo modified.templateA', 'modified.templateA',),
    )

    # Check that all context section imports are available in startup block
    # module_manager.modules['A'].import_context('on_startup')
    module_manager.modules['A'].execute(
        action='import_context',
        block='on_startup',
    )
    assert module_manager.application_context == {
        'car': {'manufacturer': 'Mercedes'},
    }

    # Double check that the other sections are not affected
    results = module_manager.modules['A'].execute(
        action='run',
        block='on_event',
    )
    assert results == (('echo on_event', 'on_event'),)

    results = module_manager.modules['A'].execute(
        action='run',
        block='on_exit',
    )
    assert results == (('echo exit', 'exit'),)

    module_manager.modules['A'].execute(
        action='import_context',
        block='on_event',
    )
    assert module_manager.application_context == {
        'car': {'manufacturer': 'Mercedes'},
    }


def test_not_using_list_when_specifiying_trigger_action(
    conf_path,
    default_global_options,
):
    application_config = {
        'module/A': {
            'on_startup': {
                'trigger': {'block': 'on_event'},
            },
            'on_event': {
                'run': [{'shell': 'echo on_event'}],
            },
        },
        '_runtime': {
            'config_directory': conf_path,
            'temp_directory': Path('/tmp/astrality'),
        },
    }
    application_config.update(default_global_options)
    module_manager = ModuleManager(application_config)

    # Check that all run commands have been imported into startup block
    result = module_manager.modules['A'].execute(
        action='run',
        block='on_startup',
    )
    assert result == (
        ('echo on_event', 'on_event',),
    )
