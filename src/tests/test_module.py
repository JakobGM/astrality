import logging
import os

from freezegun import freeze_time
import pytest

from module import Module
import timer


@pytest.fixture
def valid_module_section():
    return {
        'module/test_module': {
            'enabled': 'true',
            'timer': 'weekday',
            'template_file': '',
            'on_startup': 'echo startup',
            'on_period_change': 'echo period_change',
            'on_exit': 'echo exit',
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
                'enabled': 'false',
                'on_startup': '',
                'on_period_change': '',
                'on_exit': '',
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
        invalid_module_section.update({'module/valid2': {'enabled': 'true'}})

        with pytest.raises(RuntimeError):
            Module.valid_class_section(invalid_module_section)

    def test_module_name(self, module):
        assert module.name == 'test_module'

    def test_module_timer_class(self, module):
        assert isinstance(module.timer, timer.Weekday)

    @freeze_time('2018-01-27')
    def test_run_shell_command_with_special_expansion(self, module, caplog):
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

    @pytest.mark.skipif('TRAVIS' not in os.environ, reason='Only run on CI')
    def test_running_shell_command_that_times_out(self, module, caplog):
        module.run_shell('sleep 2.1')
        assert 'used more than 2 seconds' in caplog.record_tuples[1][2]

    def test_running_shell_command_with_non_zero_exit_code(self, module, caplog):
        module.run_shell('thiscommandshould not exist')
        assert 'non-zero return code' in caplog.record_tuples[1][2]

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

    def test_running_module_startup_command(self, module, caplog):
        module.startup()
        assert caplog.record_tuples == [
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
        valid_module_section['module/test_module'].pop('on_startup')
        module = Module(valid_module_section, conf)

        module.startup()
        assert caplog.record_tuples == [
            (
                'astrality',
                logging.DEBUG,
                '[module/test_module] No startup command specified.',
            ),
        ]

    def test_running_module_period_change_command(self, module, caplog):
        module.period_change()
        assert caplog.record_tuples == [
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
        valid_module_section['module/test_module'].pop('on_period_change')
        module = Module(valid_module_section, conf)

        module.period_change()
        assert caplog.record_tuples == [
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
        valid_module_section['module/test_module'].pop('on_exit')
        module = Module(valid_module_section, conf)

        module.exit()
        assert caplog.record_tuples == [
            (
                'astrality',
                logging.DEBUG,
                '[module/test_module] No exit command specified.',
            ),
        ]
