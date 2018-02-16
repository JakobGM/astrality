import logging
import os
import shutil
import time
from datetime import datetime, timedelta
from pathlib import Path

from freezegun import freeze_time
import pytest

from astrality import timer
from astrality.config import dict_from_config_file, generate_expanded_env_dict
from astrality.module import ContextSectionImport, Module, ModuleManager
from astrality.resolver import Resolver


@pytest.fixture
def valid_module_section():
    return {
        'module/test_module': {
            'enabled': True,
            'timer': {'type': 'weekday'},
            'templates': {
                'template_name': {
                    'source': '../tests/templates/test_template.conf',
                    'target': '/tmp/compiled_result',
                }
            },
            'on_startup': {
                'run': ['echo {period}'],
                'compile': ['template_name'],
            },
            'on_period_change': {'run': ['echo {template_name}']},
            'on_exit': {'run': ['echo exit']},
        }
    }


@pytest.fixture
def folders(conf):
    return (
        conf['_runtime']['config_directory'],
        conf['_runtime']['temp_directory'],
    )

@pytest.fixture
def simple_application_config(
    valid_module_section,
    folders,
    expanded_env_dict,
    default_global_options,
):
    config = valid_module_section.copy()
    config['_runtime'] = {}
    config['_runtime']['config_directory'], \
        config['_runtime']['temp_directory'] = folders
    config['context/env'] = expanded_env_dict
    config['context/fonts'] = {1: 'FuraMono Nerd Font'}
    config.update(default_global_options)

    # Increase run timeout, so that we can inspect the shell results
    config['settings/astrality']['run_timeout'] = 2
    return config


@pytest.fixture
def module(valid_module_section, folders):
    return Module(valid_module_section, *folders)

@pytest.fixture
def single_module_manager(simple_application_config):
    return ModuleManager(simple_application_config)


class TestModuleClass:

    def test_valid_class_section_method_with_valid_section(self, valid_module_section):
        assert Module.valid_class_section(
            section=valid_module_section,
            requires_timeout=2,
            requires_working_directory=Path('/'),
        ) == True

    def test_valid_class_section_method_with_disabled_module_section(self):
        disabled_module_section =  {
            'module/disabled_test_module': {
                'enabled': False,
                'on_startup': {'run': ['test']},
                'on_period_change': {'run': ['']},
                'on_exit': {'run': ['whatever']},
            }
        }
        assert Module.valid_class_section(
            section=disabled_module_section,
            requires_timeout=2,
            requires_working_directory=Path('/'),
        ) == False

    def test_valid_class_section_method_with_invalid_section(self):
        invalid_module_section =  {
            'context/fonts': {
                'some_key': 'some_value',
            }
        }
        assert Module.valid_class_section(
            section=invalid_module_section,
            requires_timeout=2,
            requires_working_directory=Path('/'),
        ) == False

    def test_valid_class_section_with_wrongly_sized_dict(self, valid_module_section):
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

    def test_module_timer_class(self, module):
        assert isinstance(module.timer, timer.Weekday)

    def test_using_default_static_timer_when_no_timer_is_given(self, folders):
        static_module = Module({'module/static': {}}, *folders)
        assert isinstance(static_module.timer, timer.Static)

    @freeze_time('2018-01-27')
    def test_get_shell_commands_with_special_interpolations(
        self,
        module,
        caplog,
    ):
        assert module.startup_commands() == ('echo saturday',)

        compilation_target = '/tmp/compiled_result'
        assert module.period_change_commands() == (
            f'echo {compilation_target}',
        )

    @freeze_time('2018-01-27')
    def test_running_module_manager_commands_with_special_interpolations(
        self,
        single_module_manager,
        caplog,
    ):
        single_module_manager.startup()
        assert (
            'astrality',
            logging.INFO,
            '[module/test_module] Running command "echo saturday".',
        ) in caplog.record_tuples
        assert (
            'astrality',
            logging.INFO,
            'saturday\n',
        ) in caplog.record_tuples

        caplog.clear()
        single_module_manager.period_change()
        compilation_target = '/tmp/compiled_result'
        assert (
            'astrality',
            logging.INFO,
            '[module/test_module] Running command "echo /tmp/compiled_result".',
        ) in caplog.record_tuples
        assert (
            'astrality',
            logging.INFO,
            compilation_target + '\n',
        ) in caplog.record_tuples

    @pytest.mark.slow
    def test_running_shell_command_that_times_out(self, single_module_manager, caplog):
        single_module_manager.run_shell(
            command='sleep 2.1',
            timeout=2,
            module_name='name',
        )
        assert 'used more than 2 seconds' in caplog.record_tuples[1][2]

    def test_running_shell_command_with_non_zero_exit_code(
        self,
        single_module_manager,
        caplog,
    ):
        single_module_manager.run_shell(
            command='thiscommandshould not exist',
            timeout=2,
            module_name='name',
        )
        assert 'not found' in caplog.record_tuples[1][2]
        assert 'non-zero return code' in caplog.record_tuples[2][2]

    def test_running_shell_command_with_environment_variable(
        self,
        single_module_manager,
        caplog,
    ):
        single_module_manager.run_shell(
            command='echo $USER',
            timeout=2,
            module_name='name',
        )
        assert caplog.record_tuples == [
            (
                'astrality',
                logging.INFO,
                '[module/name] Running command "echo $USER".',
            ),
            (
                'astrality',
                logging.INFO,
                os.environ['USER'] + '\n',
            )
        ]

    @freeze_time('2018-01-27')
    def test_running_module_startup_command(
        self,
        single_module_manager,
        module,
        valid_module_section,
        caplog,
    ):
        single_module_manager.startup()

        template_file = str(module.templates['template_name']['source'])
        compiled_template = str(module.templates['template_name']['target'])

        assert caplog.record_tuples == [
            (
                'astrality',
                logging.INFO,
                '[module/test_module] Running startup command.',
            ),
            (
                'astrality',
                logging.INFO,
                '[module/test_module] Running command "echo saturday".',
            ),
            (
                'astrality',
                logging.INFO,
                'saturday\n',
            )
        ]

    def test_running_module_startup_command_when_no_command_is_specified(
        self,
        simple_application_config,
        module,
        caplog,
    ):
        simple_application_config['module/test_module']['on_startup'].pop('run')
        module_manager = ModuleManager(simple_application_config)

        module_manager.startup()

        template_file = str(module.templates['template_name']['source'])
        compiled_template = str(module.templates['template_name']['target'])

        assert caplog.record_tuples == [
            (
                'astrality',
                logging.DEBUG,
                '[module/test_module] No startup command specified.',
            ),
        ]

    def test_running_module_period_change_command(
        self,
        single_module_manager,
        module,
        caplog,
    ):
        single_module_manager.period_change()

        template_file = str(module.templates['template_name']['source'])
        compiled_template = str(module.templates['template_name']['target'])

        assert caplog.record_tuples == [
            (
                'astrality',
                logging.INFO,
                '[module/test_module] Running period change command.',
            ),
            (
                'astrality',
                logging.INFO,
                f'[module/test_module] Running command "echo {compiled_template}".',
            ),
            (
                'astrality',
                logging.INFO,
                f'{compiled_template}\n',
            )
        ]

    def test_running_module_period_change_command_when_no_command_is_specified(
        self,
        simple_application_config,
        module,
        conf,
        caplog,
    ):
        simple_application_config['module/test_module']['on_period_change'].pop('run')
        module_manager = ModuleManager(simple_application_config)

        module_manager.period_change()

        template_file = str(module.templates['template_name']['source'])
        compiled_template = str(module.templates['template_name']['target'])

        assert caplog.record_tuples == [
            (
                'astrality',
                logging.DEBUG,
                '[module/test_module] No period change command specified.',
            ),
        ]

    def test_running_module_exit_command(self, single_module_manager, caplog):
        single_module_manager.exit()
        assert caplog.record_tuples == [
            (
                'astrality',
                logging.INFO,
                '[module/test_module] Running exit command.',
            ),
            (
                'astrality',
                logging.INFO,
                '[module/test_module] Running command "echo exit".',
            ),
            (
                'astrality',
                logging.INFO,
                'exit\n',
            )
        ]

    def test_running_module_exit_command_when_no_command_is_specified(
        self,
        simple_application_config,
        caplog,
    ):
        simple_application_config['module/test_module']['on_exit'].pop('run')
        module_manager = ModuleManager(simple_application_config)

        module_manager.exit()
        assert caplog.record_tuples == [
            (
                'astrality',
                logging.DEBUG,
                '[module/test_module] No exit command specified.',
            ),
        ]

    def test_location_of_template_file_defined_relatively(self, module):
        template_file = module.templates['template_name']['source']
        compiled_template = module.templates['template_name']['target']

        assert template_file.resolve() == Path(__file__).parent / 'templates' / 'test_template.conf'
        assert compiled_template == Path('/tmp/compiled_result')

    def test_location_of_template_file_defined_absolutely(
        self,
        valid_module_section,
        folders,
    ):
        absolute_path = Path(__file__).parent / 'templates' / 'test_template.conf'
        valid_module_section['module/test_module']['templates']['template_name']['source'] = absolute_path

        module = Module(valid_module_section, *folders)
        template_file = module.templates['template_name']['source']

        assert template_file == absolute_path

    def test_missing_template_file(
        self,
        valid_module_section,
        folders,
        caplog,
    ):
        valid_module_section['module/test_module']['templates']['template_name']['source'] = \
            '/not/existing'

        module = Module(valid_module_section, *folders)
        assert module.templates == {}
        assert caplog.record_tuples == [
            (
                'astrality',
                logging.ERROR,
                '[module/test_module] Template "template_name": source "/not/existing" does'
                ' not exist. Skipping compilation of this file.'
            ),
        ]

    def test_expand_path_method(self, module, conf):
        absolute_path = Path('/tmp/ast')
        tilde_path = Path('~/dir')
        relative_path = Path('test')
        assert module.expand_path(absolute_path) == absolute_path
        assert module.expand_path(tilde_path) == Path.home() / 'dir'
        assert module.expand_path(relative_path) == \
            conf['_runtime']['config_directory'] / 'test'

    def test_create_temp_file_method(self, module):
        temp_file = module.create_temp_file()
        assert temp_file.is_file()

    def test_cleanup_of_tempfile_on_exit(self, single_module_manager):
        temp_file = single_module_manager.modules['test_module'].create_temp_file()
        assert temp_file.is_file()
        single_module_manager.exit()
        assert not temp_file.is_file()

    def test_creation_of_temporary_file_when_compiled_template_is_not_defined(
        self,
        simple_application_config,
    ):
        simple_application_config['module/test_module']['templates']['template_name'].pop('target')
        module_manager = ModuleManager(simple_application_config)
        assert module_manager.modules['test_module'].templates['template_name']['target'].is_file()

    def test_compilation_of_template(
        self,
        simple_application_config,
        module,
        conf,
        caplog,
    ):
        simple_application_config['module/test_module']['timer']['type'] = 'solar'
        compiled_template_content = 'some text\n' + os.environ['USER'] + '\nFuraMono Nerd Font'
        module_manager = ModuleManager(simple_application_config)
        module_manager.compile_templates('on_startup')

        template_file = str(module.templates['template_name']['source'])
        compiled_template = str(module.templates['template_name']['target'])

        with open('/tmp/compiled_result', 'r') as file:
            compiled_result = file.read()

        assert compiled_template_content == compiled_result
        assert caplog.record_tuples == [
            (
                'astrality',
                logging.INFO,
                f'[Compiling] Template: "{template_file}" -> Target: "{compiled_template}"'
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
    module_manager.finish_tasks()

    # Only startup commands should be finished at first
    template = str(module_manager.modules['test_module'].templates['template_name']['source'])
    assert caplog.record_tuples == [
        (
            'astrality',
            logging.INFO,
            f'[Compiling] Template: "{template}" -> Target: "/tmp/compiled_result"'
        ),
        (
            'astrality',
            logging.INFO,
            '[module/test_module] Running startup command.',
        ),
        (
            'astrality',
            logging.INFO,
            '[module/test_module] Running command "echo thursday".',
        ),
        (
            'astrality',
            logging.INFO,
            'thursday\n',
        ),
    ]

    # Now move one day ahead, and observe if period change commands are run
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
            '[module/test_module] Running period change command.',
        ),
        (
            'astrality',
            logging.INFO,
            '[module/test_module] Running command "echo /tmp/compiled_result".',
        ),
        (
            'astrality',
            logging.INFO,
            '/tmp/compiled_result\n',
        )
    ]


def test_has_unfinished_tasks(simple_application_config, freezer):
    # Move time to midday
    midday = datetime.now().replace(hour=12, minute=0)
    freezer.move_to(midday)

    # At instanziation, the module should have unfinished tasks
    weekday_module = ModuleManager(simple_application_config)
    assert weekday_module.has_unfinished_tasks() == True

    # After finishing tasks, there should be no unfinished tasks (duh!)
    weekday_module.finish_tasks()
    assert weekday_module.has_unfinished_tasks() == False

    # If we move the time forwards, but not to a new period, there should still
    # not be any unfinished tasks
    before_midnight = datetime.now().replace(hour=23, minute=59)
    freezer.move_to(before_midnight)
    assert weekday_module.has_unfinished_tasks() == False

    # But right after a period change (new weekday), there should be unfinished
    # tasks
    two_minutes = timedelta(minutes=2)
    freezer.move_to(before_midnight + two_minutes)
    assert weekday_module.has_unfinished_tasks() == True

    # Again, after finishing tasks, there should be no unfinished tasks left
    weekday_module.finish_tasks()
    assert weekday_module.has_unfinished_tasks() == False



@pytest.fixture
def config_with_modules(default_global_options):
    return {
        'settings/astrality': default_global_options['settings/astrality'],
        'context/env': generate_expanded_env_dict(),
        'module/solar_module': {
            'enabled': True,
            'timer': {
                'type': 'solar',
                'longitude': 0,
                'latitude': 0,
                'elevation': 0,
            },
            'templates': {
                'template_name': {
                    'source': 'astrality/tests/templates/test_template.conf',
                    'target': '/tmp/compiled_result',
                }
            },
            'on_startup': {'run': ['echo solar compiling {template_name}']},
            'on_period_change': {'run': ['echo solar {period}']},
            'on_exit': {'run': ['echo solar exit']},
        },
        'module/weekday_module': {
            'enabled': True,
            'timer': {'type': 'weekday'},
            'on_startup': {'run': ['echo weekday startup']},
            'on_period_change': {'run': ['echo weekday {period}']},
            'on_exit': {'run': ['echo weekday exit']},
        },
        'module/disabled_module': {
            'enabled': False,
            'timer': 'static',
        },
        'context/fonts': {1: 'FuraCode Nerd Font'},
        '_runtime': {
            'config_directory': Path(__file__).parents[2],
            'temp_directory': '/tmp',
        }
    }

@pytest.fixture
def module_manager(config_with_modules):
    return ModuleManager(config_with_modules)


def test_import_sections_on_period_change(config_with_modules, freezer):
    config_with_modules['module/weekday_module']['on_period_change']['import_context'] = [{
        'to_section': 'week',
        'from_file': 'astrality/tests/templates/weekday.yaml',
        'from_section': '{period}',
    }]
    config_with_modules.pop('module/solar_module')
    module_manager = ModuleManager(config_with_modules)

    assert module_manager.application_context['fonts'] == {1: 'FuraCode Nerd Font'}

    sunday = datetime(year=2018, month=2, day=4)
    freezer.move_to(sunday)
    module_manager.finish_tasks()

    # Make application_context comparisons easier
    module_manager.application_context.pop('env')

    # Startup does not count as a period change, so no context has been imported
    assert module_manager.application_context == {
        'fonts': Resolver({1: 'FuraCode Nerd Font'}),
    }

    monday = datetime(year=2018, month=2, day=5)
    freezer.move_to(monday)
    module_manager.finish_tasks()

    # The period has now changed, so context should be imported
    assert module_manager.application_context == {
        'fonts': Resolver({1: 'FuraCode Nerd Font'}),
        'week': Resolver({'day': 'monday'}),
    }

def test_compiling_templates_on_cross_of_module_boundries(default_global_options):
    module_A = {
        'templates': {
            'template_A': {
                'source': '../tests/templates/no_context.template',
            },
        },
    }
    modules_config = {
        'module/A': module_A,
        '_runtime': {
            'config_directory': Path(__file__).parent,
            'temp_directory': Path('/tmp'),
        },
    }
    modules_config.update(default_global_options)

    module_manager = ModuleManager(modules_config)
    module_manager.finish_tasks()

    # Modules should not compile their templates unless they explicitly
    # define a compile string in a on_* block.
    with open(module_manager.modules['A'].templates['template_A']['target']) as compilation:
        assert compilation.read() == ''

    # We now insert another module, B, which compiles the template of the
    # previous module, A
    module_B = {
        'on_startup': {
            'compile': ['A.template_A'],
        },
    }
    modules_config['module/B'] = module_B
    module_manager = ModuleManager(modules_config)
    module_manager.finish_tasks()
    with open(module_manager.modules['A'].templates['template_A']['target']) as compilation:
        assert compilation.read() == 'one\ntwo\nthree'


def test_import_sections_on_startup(config_with_modules, freezer):
    # Insert day the module was started into 'start day'
    config_with_modules['module/weekday_module']['on_startup']['import_context'] = [{
        'to_section': 'start_day',
        'from_file': 'astrality/tests/templates/weekday.yaml',
        'from_section': '{period}',
    }]

    # Insert the current day into 'day_now'
    config_with_modules['module/weekday_module']['on_period_change']['import_context'] = [{
        'to_section': 'day_now',
        'from_file': 'astrality/tests/templates/weekday.yaml',
        'from_section': '{period}',
    }]
    config_with_modules.pop('module/solar_module')
    module_manager = ModuleManager(config_with_modules)

    # Remove 'env' context for easier comparisons
    module_manager.application_context.pop('env')

    # Before finishing tasks, no context sections are imported
    assert module_manager.application_context['fonts'] == {1: 'FuraCode Nerd Font'}

    # Start module on a monday
    sunday = datetime(year=2018, month=2, day=4)
    freezer.move_to(sunday)
    module_manager.finish_tasks()
    assert module_manager.application_context == {
        'fonts': Resolver({1: 'FuraCode Nerd Font'}),
        'start_day': Resolver({'day': 'sunday'}),
    }

    # 'now_day' should now be added, but 'start_day' should remain unchanged
    monday = datetime(year=2018, month=2, day=5)
    freezer.move_to(monday)
    module_manager.finish_tasks()
    assert module_manager.application_context == {
        'fonts': Resolver({1: 'FuraCode Nerd Font'}),
        'start_day': Resolver({'day': 'sunday'}),
        'day_now': Resolver({'day': 'monday'}),
    }


def test_context_section_imports(folders):
    module_config = {
        'module/name': {
            'on_startup': {
                'import_context': [
                    {
                        'from_file': '/testfile',
                        'from_section': 'source_section',
                        'to_section': 'target_section',
                    }
                ]
            },
            'on_period_change': {
                'import_context': [
                    {
                        'from_file': '/testfile',
                        'from_section': 'source_section',
                    }
                ]
            },
        },
    }
    module = Module(module_config, *folders)
    startup_csis = module.context_section_imports('on_startup')
    expected = (
        ContextSectionImport(
            from_config_file=Path('/testfile'),
            from_section='source_section',
            into_section='target_section',
        ),
    )
    assert startup_csis == expected

    period_change_csis = module.context_section_imports('on_period_change')
    expected = (
        ContextSectionImport(
            from_config_file=Path('/testfile'),
            from_section='source_section',
            into_section='source_section',
        ),
    )
    assert period_change_csis == expected


class TestModuleManager:
    def test_invocation_of_module_manager_with_config(self, conf):
        ModuleManager(conf)

    @pytest.mark.slow
    def test_using_finish_tasks_on_example_configuration(self, conf):
        module_manager = ModuleManager(conf)
        module_manager.finish_tasks()

    def test_number_of_modules_instanziated_by_module_manager(self, module_manager):
        assert len(module_manager) == 2


def test_time_until_next_period_of_several_modules(config_with_modules, module_manager, freezer):
    solar_timer = timer.Solar(config_with_modules)
    noon = solar_timer.location.sun()['noon']

    one_minute = timedelta(minutes=1)
    freezer.move_to(noon - one_minute)

    assert module_manager.time_until_next_period() == one_minute
    two_minutes_before_midnight = datetime.now().replace(hour=23, minute=58)
    freezer.move_to(two_minutes_before_midnight)

    assert module_manager.time_until_next_period().total_seconds() == \
                              timedelta(minutes=2).total_seconds()

def test_detection_of_new_period_involving_several_modules(
    config_with_modules,
    freezer,
):
    # Move time to right before noon
    solar_timer = timer.Solar(config_with_modules)
    noon = solar_timer.location.sun()['noon']
    one_minute = timedelta(minutes=1)
    freezer.move_to(noon - one_minute)
    module_manager = ModuleManager(config_with_modules)

    # All modules should now considered period changed
    assert module_manager.has_unfinished_tasks() == True

    # Running period change method for all the period changed modules
    module_manager.finish_tasks()

    # After running these methods, they should all be reverted to not changed
    assert module_manager.has_unfinished_tasks() == False

    # Move time to right after noon
    freezer.move_to(noon + one_minute)

    # The solar timer should now be considered to have been period changed
    assert module_manager.has_unfinished_tasks() == True

    # Again, check if period_change() method makes them unchanged
    module_manager.finish_tasks()
    assert module_manager.has_unfinished_tasks() == False

    # Move time two days forwards
    two_days = timedelta(days=2)
    freezer.move_to(noon + two_days)

    # Now both timers should be considered period changed
    assert module_manager.has_unfinished_tasks() == True

def test_that_shell_filter_is_run_from_config_directory(
    conf_path,
    default_global_options,
):
    shell_filter_template = Path(__file__).parent / 'templates' / 'shell_filter_working_directory.template'
    shell_filter_template_target = Path('/tmp/astrality/shell_filter_working_directory.template')
    config = {
        'module/A': {
            'templates': {
                'shell_filter_template': {
                    'source': str(shell_filter_template),
                    'target': str(shell_filter_template_target),
                },
            },
            'on_startup': {
                'compile': ['shell_filter_template'],
            },
        },
        '_runtime': {
            'config_directory': conf_path,
            'temp_directory': Path('/tmp/astrality'),
        },
    }
    config.update(default_global_options)
    module_manager = ModuleManager(config)
    module_manager.compile_templates('on_startup')

    with open(shell_filter_template_target) as compiled:
        assert compiled.read() == str(conf_path)

    os.remove(shell_filter_template_target)


@pytest.yield_fixture
def modules_config(conf_path, default_global_options):
    empty_template = Path(__file__).parent / 'templates' / 'empty.template'
    empty_template_target = Path('/tmp/astrality/empty_temp_template')
    temp_directory = Path('/tmp/astrality')
    touch_target = temp_directory / 'touched'

    secondary_template = Path(__file__).parent / 'templates' / 'no_context.template'
    secondary_template_target = temp_directory / 'secondary_template.tmp'

    config = {
        'module/A': {
            'templates': {
                'template1': {
                    'source': str(empty_template),
                    'target': str(empty_template_target),
                },
            },
            'on_modified': {
                'template1': {
                    'compile': ['template1', 'B.template1'],
                    'run': ['touch ' + str(touch_target)],
                },
            },
        },
        'module/B': {
            'templates': {
                'template1': {
                    'source': str(secondary_template),
                    'target': str(secondary_template_target),
                },
            },
        },
        '_runtime': {
            'config_directory': Path(__file__).parent,
            'temp_directory': temp_directory,
        }
    }
    config.update(default_global_options)
    yield (
        config,
        empty_template,
        empty_template_target,
        touch_target,
        secondary_template,
        secondary_template_target,
    )

    # Cleanup all test files for next test iteration
    if empty_template.is_file():
        empty_template.write_text('')
    if empty_template_target.is_file():
        os.remove(empty_template_target)
    if secondary_template_target.is_file():
        os.remove(secondary_template_target)
    if touch_target.is_file():
        os.remove(touch_target)

class TestModuleFileWatching:
    def test_modified_commands_of_module(self, modules_config):
        config, empty_template, empty_template_target, touch_target, *_= modules_config
        module_manager = ModuleManager(config)
        assert module_manager.modules['A'].modified_commands('template1') == \
            ('touch ' + str(touch_target), )

    def test_direct_invocation_of_modifed_method_of_module_manager(self, modules_config):
        (
            config,
            empty_template,
            empty_template_target,
            touch_target,
            secondary_template,
            secondary_template_target,
        ) = modules_config
        module_manager = ModuleManager(config)

        # PS: Disabling the directory watcher is not necessary, as it is done in
        # the startup method.

        # Now write new text to the template
        empty_template.write_text('new content')

        # And trigger the modified method manually
        module_manager.modified(empty_template)

        # And assert that the new template has been compiled
        assert empty_template_target.is_file()
        with open(empty_template_target) as file:
            assert file.read() == 'new content'

        # And that the new file has been touched
        time.sleep(0.5)
        assert touch_target.is_file()

    def test_on_modified_event_in_module(self, modules_config):
        (
            config,
            empty_template,
            empty_template_target,
            touch_target,
            secondary_template,
            secondary_template_target,
        ) = modules_config
        module_manager = ModuleManager(config)

        # Start the file watcher by invoking the startup command indirectly
        # through finish_tasks() method
        module_manager.finish_tasks()

        # Assert that the template file is really empty as a sanity check
        with open(empty_template) as file:
            assert file.read() == ''

        # And that target files are not created yet
        assert not touch_target.is_file()
        assert not empty_template_target.is_file()
        assert not secondary_template_target.is_file()

        # Trigger the on_modified event
        empty_template.write_text('new content')
        time.sleep(1)

        # And assert that the new template has been compiled
        assert empty_template_target.is_file()
        with open(empty_template_target) as file:
            assert file.read() == 'new content'

        # Assert that also templates from other modules are compiled
        assert secondary_template_target.is_file()
        with open(secondary_template_target) as file:
            assert file.read() == 'one\ntwo\nthree'

        # And that the new file has been touched
        assert touch_target.is_file()

    @pytest.yield_fixture
    def test_template_targets(self):
        template_target1 = Path('/tmp/astrality/target1')
        template_target2 = Path('/tmp/astrality/target2')

        yield template_target1, template_target2

        if template_target1.is_file():
            os.remove(template_target1)
        if template_target2.is_file():
            os.remove(template_target2)

    @pytest.mark.slow
    def test_hot_reloading(self, test_template_targets, default_global_options):
        template_target1, template_target2 = test_template_targets
        config_dir = Path(__file__).parent / 'test_config'
        config1 = config_dir / 'astrality1.yaml'
        config2 = config_dir / 'astrality2.yaml'
        target_config = config_dir / 'astrality.yaml'
        temp_directory = Path('/tmp/astrality')

        # Copy the first configuration into place
        shutil.copy(str(config1), str(target_config))

        application_config1 = dict_from_config_file(config1)
        application_config1['_runtime'] = {
            'config_directory': config_dir,
            'temp_directory': temp_directory,
        }
        application_config1.update(default_global_options)
        application_config1['settings/astrality']['hot_reload'] = True

        module_manager = ModuleManager(application_config1)

        # Before beginning, the template should not be compiled
        assert not template_target1.is_file()

        # But when we finalize tasks, it should be compiled
        module_manager.finish_tasks()
        assert template_target1.is_file()

        # Also check that the filewatcher has been started
        assert module_manager.directory_watcher.observer.is_alive()

        # We now "edit" the configuration file
        shutil.copy(str(config2), str(target_config))
        time.sleep(0.7)

        # Since hot reloading is enabled, the new template target should be
        # compiled, and the old one cleaned up
        assert template_target2.is_file()
        assert not template_target1.is_file()

        # And we switch back again
        shutil.copy(str(config1), str(target_config))
        time.sleep(0.7)
        assert template_target1.is_file()
        assert not template_target2.is_file()

        # Cleanup config file
        if target_config.is_file():
            os.remove(target_config)



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
    conf_path,
    default_global_options,
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
            'timer': {'type': 'weekday'},
            'on_startup': {
                'run': ['touch ' + str(test_file1)],
            },
            'on_period_change': {
                'run': ['touch ' + str(test_file2)],
            },
        },
        '_runtime': {
            'config_directory': conf_path,
            'temp_directory': Path('/tmp/astrality'),
        },
    }
    application_config.update(default_global_options)
    module_manager = ModuleManager(application_config)

    # Before call to finish_tasks, no actions should have been performed
    assert not test_file1.is_file() and not test_file2.is_file()

    # Now call finish_tasks for the first time, only startup event block should
    # be run
    module_manager.finish_tasks()
    time.sleep(0.5)
    assert test_file1.is_file()
    assert not test_file2.is_file()

    friday = datetime(
        year=2018,
        month=2,
        day=16,
        hour=12,
    )

def test_trigger_event_module_action(conf_path, default_global_options):
    application_config = {
        'module/A': {
            'timer': {'type': 'weekday'},
            'on_startup': {
                'trigger': ['on_period_change', 'on_exit', 'on_modified.templateA'],
                'run': ['echo startup'],
            },
            'on_period_change': {
                'run': ['echo period_change'],
                'import_context': [{
                    'from_file': 'contexts/file.yaml',
                    'from_section': 'section',
                }],
            },
            'on_exit': {
                'run': ['echo exit'],
            },
            'on_modified': {
                'templateA': {
                    'run': ['echo modified.templateA'],
                    'compile': ['templateA'],
                },
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
    assert module_manager.modules['A'].startup_commands() == (
        'echo startup',
        'echo period_change',
        'echo exit',
        'echo modified.templateA',
    )

    # Check that all context section imports are available in startup block
    assert module_manager.modules['A'].context_section_imports('on_startup') == (
        ContextSectionImport(
            into_section='section',
            from_section='section',
            from_config_file=conf_path / 'contexts' / 'file.yaml',
        ),
    )

    # Check that all compile actions have been merged into startup block
    assert module_manager.modules['A'].module_config['on_startup']['compile'] ==\
        ['templateA']

    # Double check that the other sections are not affected
    assert module_manager.modules['A'].period_change_commands() == (
        'echo period_change',
    )
    assert module_manager.modules['A'].exit_commands() == (
        'echo exit',
    )

    assert module_manager.modules['A'].context_section_imports('on_period_change') == (
        ContextSectionImport(
            into_section='section',
            from_section='section',
            from_config_file=conf_path / 'contexts' / 'file.yaml',
        ),
    )

def test_not_using_list_when_specifiying_trigger_action(
    conf_path,
    default_global_options,
):
    application_config = {
        'module/A': {
            'on_startup': {
                'trigger': 'on_period_change',
            },
            'on_period_change': {
                'run': ['echo period_change'],
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
    assert module_manager.modules['A'].startup_commands() == (
        'echo period_change',
    )
