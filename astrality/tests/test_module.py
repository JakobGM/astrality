from datetime import datetime, timedelta
import logging
import os
from pathlib import Path

from freezegun import freeze_time
import pytest

from astrality import timer
from astrality.config import generate_expanded_env_dict
from astrality.module import Module, ModuleManager
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
            'run_on_startup': ['echo {period}'],
            'run_on_period_change': ['echo {template_name}'],
            'run_on_exit': ['echo exit'],
        }
    }


@pytest.fixture
def folders(conf):
    return (
        conf['_runtime']['config_directory'],
        conf['_runtime']['temp_directory'],
    )

@pytest.fixture
def simple_application_config(valid_module_section, folders, expanded_env_dict):
    config = valid_module_section.copy()
    config['_runtime'] = {}
    config['_runtime']['config_directory'], \
        config['_runtime']['temp_directory'] = folders
    config['context/env'] = expanded_env_dict
    config['context/fonts'] = {1: 'FuraMono Nerd Font'}
    return config


@pytest.fixture
def module(valid_module_section, folders):
    return Module(valid_module_section, *folders)

@pytest.fixture
def single_module_manager(simple_application_config):
    return ModuleManager(simple_application_config)


class TestModuleClass:

    def test_valid_class_section_method_with_valid_section(self, valid_module_section):
        assert Module.valid_class_section(valid_module_section) == True

    def test_valid_class_section_method_with_disabled_module_section(self):
        disabled_module_section =  {
            'module/disabled_test_module': {
                'enabled': False,
                'run_on_startup': ['test'],
                'run_on_period_change': [''],
                'run_on_exit': ['whatever'],
            }
        }
        assert Module.valid_class_section(disabled_module_section) == False

    def test_valid_class_section_method_with_invalid_section(self):
        invalid_module_section =  {
            'context/fonts': {
                'some_key': 'some_value',
            }
        }
        assert Module.valid_class_section(invalid_module_section) == False

    def test_valid_class_section_with_wrongly_sized_dict(self, valid_module_section):
        invalid_module_section = valid_module_section
        invalid_module_section.update({'module/valid2': {'enabled': True}})

        with pytest.raises(RuntimeError):
            Module.valid_class_section(invalid_module_section)

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
        single_module_manager.run_shell('sleep 2.1', 'name')
        assert 'used more than 2 seconds' in caplog.record_tuples[1][2]

    def test_running_shell_command_with_non_zero_exit_code(
        self,
        single_module_manager,
        caplog,
    ):
        single_module_manager.run_shell('thiscommandshould not exist', 'name')
        assert 'not found' in caplog.record_tuples[1][2]
        assert 'non-zero return code' in caplog.record_tuples[2][2]

    def test_running_shell_command_with_environment_variable(
        self,
        single_module_manager,
        caplog,
    ):
        single_module_manager.run_shell('echo $USER', 'name')
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
        simple_application_config['module/test_module'].pop('run_on_startup')
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
        simple_application_config['module/test_module'].pop('run_on_period_change')
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
        simple_application_config['module/test_module'].pop('run_on_exit')
        module_manager = ModuleManager(simple_application_config)

        module_manager.exit()
        assert caplog.record_tuples == [
            (
                'astrality',
                logging.DEBUG,
                '[module/test_module] No exit command specified.',
            ),
        ]

    @freeze_time('2018-02-05')
    def test_running_finished_tasks_command(
        self,
        simple_application_config,
        caplog,
    ):
        """Test that every task is finished at first finish_tasks() invocation."""
        module_manager = ModuleManager(simple_application_config)
        module_manager.finish_tasks()
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
                '[module/test_module] Running command "echo monday".',
            ),
            (
                'astrality',
                logging.INFO,
                'monday\n',
            ),
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
        module_manager.compile_templates()

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
def config_with_modules():
    return {
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
            'on_startup': ['echo solar compiling {template_name}'],
            'on_period_change': ['echo solar {period}'],
            'on_exit': ['echo solar exit'],
        },
        'module/weekday_module': {
            'enabled': True,
            'timer': {'type': 'weekday'},
            'on_startup': ['echo weekday startup'],
            'on_period_change': ['echo weekday {period}'],
            'on_exit': ['echo weekday exit'],
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
    config_with_modules['module/weekday_module']['import_context_sections_on_period_change'] = \
        ['week astrality/tests/templates/weekday.yaml {period}']
    module_manager = ModuleManager(config_with_modules)

    assert 'env' in module_manager.application_context
    assert module_manager.application_context['fonts'] == {1: 'FuraCode Nerd Font'}

    monday = datetime(year=2018, month=2, day=5)
    freezer.move_to(monday)
    module_manager.finish_tasks()
    module_manager.application_context.pop('env')
    assert module_manager.application_context == {
        'fonts': Resolver({1: 'FuraCode Nerd Font'}),
        'week': Resolver({'day': 'monday'}),
    }


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
