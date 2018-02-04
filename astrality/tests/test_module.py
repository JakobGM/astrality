from datetime import datetime, timedelta
import logging
import os
from pathlib import Path

from freezegun import freeze_time
import pytest

from astrality.config import generate_expanded_env_dict
from astrality.module import Module, ModuleManager
from astrality import timer


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
            'run_on_startup': ['echo startup'],
            'run_on_period_change': ['echo period_change'],
            'run_on_exit': ['echo exit'],
        }
    }

@pytest.fixture
def module(valid_module_section, conf):
    return Module(valid_module_section, conf)


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
            'general/fonts': {
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

    def test_using_default_static_timer_when_no_timer_is_given(self, conf):
        static_module = Module({'module/static': {}}, conf)
        assert isinstance(static_module.timer, timer.Static)

    @freeze_time('2018-01-27')
    def test_run_shell_command_with_special_expansions(self, module, caplog):
        module.run_shell('echo {period}')
        assert caplog.record_tuples == [
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

        caplog.clear()
        module.run_shell('echo {template_name}')
        compilation_target = '/tmp/compiled_result'
        assert caplog.record_tuples == [
            (
                'astrality',
                logging.INFO,
                '[module/test_module] Running command "echo /tmp/compiled_result".',
            ),
            (
                'astrality',
                logging.INFO,
                compilation_target + '\n',
            )
        ]

    @pytest.mark.slow
    def test_running_shell_command_that_times_out(self, module, caplog):
        module.run_shell('sleep 2.1')
        assert 'used more than 2 seconds' in caplog.record_tuples[1][2]

    def test_running_shell_command_with_non_zero_exit_code(self, module, caplog):
        module.run_shell('thiscommandshould not exist')
        assert 'not found' in caplog.record_tuples[1][2]
        assert 'non-zero return code' in caplog.record_tuples[2][2]

    def test_running_shell_command_with_environment_variable(self, module, caplog):
        module.run_shell('echo $USER')
        assert caplog.record_tuples == [
            (
                'astrality',
                logging.INFO,
                '[module/test_module] Running command "echo $USER".',
            ),
            (
                'astrality',
                logging.INFO,
                os.environ['USER'] + '\n',
            )
        ]

    def test_running_module_startup_command(
        self,
        module,
        valid_module_section,
        caplog,
    ):
        module.startup()

        template_file = str(module.templates['template_name']['source'])
        compiled_template = str(module.templates['template_name']['target'])

        assert caplog.record_tuples == [
            (
                'astrality',
                logging.INFO,
                f'[Compiling] Template: "{template_file}" -> Target: "{compiled_template}"',
            ),
            (
                'astrality',
                logging.INFO,
                '[module/test_module] Running startup command.',
            ),
            (
                'astrality',
                logging.INFO,
                '[module/test_module] Running command "echo startup".',
            ),
            (
                'astrality',
                logging.INFO,
                'startup\n',
            )
        ]

    def test_running_module_startup_command_when_no_command_is_specified(
        self,
        valid_module_section,
        conf,
        caplog,
    ):
        valid_module_section['module/test_module'].pop('run_on_startup')
        module = Module(valid_module_section, conf)

        module.startup()

        template_file = str(module.templates['template_name']['source'])
        compiled_template = str(module.templates['template_name']['target'])

        assert caplog.record_tuples == [
            (
                'astrality',
                logging.INFO,
                f'[Compiling] Template: "{template_file}" -> Target: "{compiled_template}"',
            ),
            (
                'astrality',
                logging.DEBUG,
                '[module/test_module] No startup command specified.',
            ),
        ]

    def test_running_module_period_change_command(
        self,
        module,
        valid_module_section,
        caplog,
    ):
        module.period_change()

        template_file = str(module.templates['template_name']['source'])
        compiled_template = str(module.templates['template_name']['target'])

        assert caplog.record_tuples == [
            (
                'astrality',
                logging.INFO,
                f'[Compiling] Template: "{template_file}" -> Target: "{compiled_template}"',
            ),
            (
                'astrality',
                logging.INFO,
                '[module/test_module] Running period change command.',
            ),
            (
                'astrality',
                logging.INFO,
                '[module/test_module] Running command "echo period_change".',
            ),
            (
                'astrality',
                logging.INFO,
                'period_change\n',
            )
        ]

    def test_running_module_period_change_command_when_no_command_is_specified(
        self,
        valid_module_section,
        conf,
        caplog,
    ):
        valid_module_section['module/test_module'].pop('run_on_period_change')
        module = Module(valid_module_section, conf)

        module.period_change()

        template_file = str(module.templates['template_name']['source'])
        compiled_template = str(module.templates['template_name']['target'])

        assert caplog.record_tuples == [
            (
                'astrality',
                logging.INFO,
                f'[Compiling] Template: "{template_file}" -> Target: "{compiled_template}"',
            ),
            (
                'astrality',
                logging.DEBUG,
                '[module/test_module] No period change command specified.',
            ),
        ]

    def test_running_module_exit_command(self, module, caplog):
        module.exit()
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
        valid_module_section,
        conf,
        caplog,
    ):
        valid_module_section['module/test_module'].pop('run_on_exit')
        module = Module(valid_module_section, conf)

        module.exit()
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
        conf,
    ):
        absolute_path = Path(__file__).parent / 'templates' / 'test_template.conf'
        valid_module_section['module/test_module']['templates']['template_name']['source'] = absolute_path

        module = Module(valid_module_section, conf)
        template_file = module.templates['template_name']['source']

        assert template_file == absolute_path

    def test_missing_template_file(
        self,
        valid_module_section,
        conf,
        caplog,
    ):
        valid_module_section['module/test_module']['templates']['template_name']['source'] = \
            '/not/existing'

        module = Module(valid_module_section, conf)
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

    def test_cleanup_of_tempfile_on_exit(self, module):
        temp_file = module.create_temp_file()
        module.exit()
        assert not temp_file.is_file()

    def test_creation_of_temporary_file_when_compiled_template_is_not_defined(
        self,
        valid_module_section,
        conf,
    ):
        valid_module_section['module/test_module']['templates']['template_name'].pop('target')
        module = Module(valid_module_section, conf)
        assert module.templates['template_name']['target'].is_file()

    def test_compilation_of_template(
        self,
        valid_module_section,
        conf,
        caplog,
    ):
        valid_module_section['module/test_module']['timer']['type'] = 'solar'
        compiled_template_content = 'some text\n' + os.environ['USER'] + '\nFuraMono Nerd Font'
        module = Module(valid_module_section, conf)
        module.compile_templates()

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

def test_has_unfinished_tasks(valid_module_section, conf, freezer):
    # Move time to midday
    midday = datetime.now().replace(hour=12, minute=0)
    freezer.move_to(midday)

    # At instanziation, the module should have unfinished tasks
    weekday_module = Module(valid_module_section, conf)
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
        'env': generate_expanded_env_dict(),
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
                    'source': 'src/tests/templates/test_template.conf',
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
        'fonts': {1: 'FuraCode Nerd Font'},
        '_runtime': {
            'config_directory': Path(__file__).parents[2],
        }
    }

@pytest.fixture
def module_manager(config_with_modules):
    return ModuleManager(config_with_modules)


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

    # Get period changed modules right after ModuleManager instanziation
    module_manager = ModuleManager(config_with_modules)
    modules_with_unfinished_tasks = tuple(module_manager.modules_with_unfinished_tasks())

    # All modules should now considered period changed
    assert module_manager.has_unfinished_tasks() == True
    assert len(tuple(modules_with_unfinished_tasks)) == 2

    # Running period change method for all the period changed modules
    module_manager.finish_tasks()

    # After running these methods, they should all be reverted to not changed
    assert module_manager.has_unfinished_tasks() == False
    assert len(tuple(module_manager.modules_with_unfinished_tasks())) == 0

    # Move time to right after noon
    freezer.move_to(noon + one_minute)

    # The solar timer should now be considered to have been period changed
    modules_with_unfinished_tasks = tuple(module_manager.modules_with_unfinished_tasks())
    assert module_manager.has_unfinished_tasks() == True
    assert len(modules_with_unfinished_tasks) == 1
    assert isinstance(modules_with_unfinished_tasks[0].timer, timer.Solar)

    # Again, check if period_change() method makes them unchanged
    module_manager.finish_tasks()
    assert module_manager.has_unfinished_tasks() == False
    assert len(tuple(module_manager.modules_with_unfinished_tasks())) == 0

    # Move time two days forwards
    two_days = timedelta(days=2)
    freezer.move_to(noon + two_days)

    # Now both timers should be considered period changed
    assert module_manager.has_unfinished_tasks() == True
    assert len(tuple(module_manager.modules_with_unfinished_tasks())) == 2
