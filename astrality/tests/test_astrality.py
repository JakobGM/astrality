import logging
import os
import psutil
import signal
import subprocess
import time

import pytest

from astrality.astrality import main, kill_old_astrality_processes
from astrality import utils
from astrality.tests.utils import Retry
from astrality.xdg import XDG


@pytest.mark.slow
def test_termination_of_main_process():
    astrality_process = subprocess.Popen(
        ['./bin/astrality'],
        stdout=subprocess.PIPE,
        preexec_fn=os.setsid,
    )

    time.sleep(2)
    os.killpg(os.getpgid(astrality_process.pid), signal.SIGTERM)

    astrality_process.wait()
    assert astrality_process.returncode == 0


@pytest.mark.slow
def test_interrupt_of_main_process():
    astrality_process = subprocess.Popen(
        ['./bin/astrality'],
        stdout=subprocess.PIPE,
        preexec_fn=os.setsid,
    )

    time.sleep(2)
    os.killpg(os.getpgid(astrality_process.pid), signal.SIGINT)

    astrality_process.wait()
    assert astrality_process.returncode == 0


def test_enabling_specific_module_from_command_line(
    caplog,
    monkeypatch,
    test_config_directory,
):
    """Modules parameter to main should enable specific module(s)."""
    monkeypatch.setitem(
        os.environ,
        'ASTRALITY_CONFIG_HOME',
        str(test_config_directory),
    )
    main(modules=['../test_modules/two_modules::bangladesh'], test=True)

    assert (
        'astrality.utils',
        logging.INFO,
        'Greetings from Dhaka!',
    ) in caplog.record_tuples


class TestKillOldAstralityProcesses:
    """Tests for astrality.astrality.kill_old_astrality_processes."""

    def test_killing_old_running_process(self):
        """The same running process should be killed."""
        perpetual_process = psutil.Popen([
            'python',
            '-c',
            '"from time import sleep; sleep(9999999999999)"',
        ])
        pidfile = XDG().data('astrality.pid')
        utils.dump_yaml(
            data=perpetual_process.as_dict(
                attrs=['pid', 'create_time', 'username'],
            ),
            path=pidfile,
        )
        kill_old_astrality_processes()
        assert Retry()(lambda: not perpetual_process.is_running())

    def test_not_killing_new_procces_with_same_pid(self):
        """The process should not be killed when it is not the original saved"""
        perpetual_process = psutil.Popen([
            'python',
            '-c',
            '"from time import sleep; sleep(9999999999999)"',
        ])

        process_data = perpetual_process.as_dict(
            attrs=['pid', 'create_time', 'username'],
        )
        process_data['create_time'] += 1

        utils.dump_yaml(
            data=process_data,
            path=XDG().data('astrality.pid'),
        )
        kill_old_astrality_processes()
        assert Retry()(lambda: perpetual_process.is_running())
        perpetual_process.kill()

    def test_trying_to_kill_process_no_longer_running(self):
        """No longer running processes should be handled gracefully."""
        finished_process = psutil.Popen(['echo', 'Done!'])
        process_data = finished_process.as_dict(
            attrs=['pid', 'create_time', 'username'],
        )
        finished_process.wait()

        utils.dump_yaml(
            data=process_data,
            path=XDG().data('astrality.pid'),
        )
        kill_old_astrality_processes()

    def test_killing_processes_when_no_previous_command_has_been_run(self):
        """The first ever invocation of the function should be handled."""
        pidfile = XDG().data('astrality.pid')
        pidfile.unlink()
        kill_old_astrality_processes()
        assert utils.load_yaml(
            path=pidfile,
        ) == psutil.Process().as_dict(
            attrs=['pid', 'create_time', 'username'],
        )
