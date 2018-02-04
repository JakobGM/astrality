import os
import signal
import subprocess
import time

import pytest

from astrality.astrality import main


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

@pytest.mark.slow
def test_invocation_of_main_process():
    main(test=True)
