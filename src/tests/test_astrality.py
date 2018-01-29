import os
from pathlib import Path
import signal
import subprocess
import time

import pytest

from astrality import main


@pytest.mark.skipif('TRAVIS' not in os.environ, reason='Only run on CI')
def test_termination_of_main_process():
    astrality_process = subprocess.Popen(
        ['python3', Path(Path(__file__).parents[1], 'astrality.py', )],
        stdout=subprocess.PIPE,
        preexec_fn=os.setsid,
    )

    time.sleep(2)
    os.killpg(os.getpgid(astrality_process.pid), signal.SIGTERM)

    astrality_process.wait()
    assert astrality_process.returncode == 0


@pytest.mark.skipif('TRAVIS' not in os.environ, reason='Only run on CI')
def test_interrupt_of_main_process():
    astrality_process = subprocess.Popen(
        ['python3', Path(Path(__file__).parents[1], 'astrality.py', )],
        stdout=subprocess.PIPE,
        preexec_fn=os.setsid,
    )

    time.sleep(2)
    os.killpg(os.getpgid(astrality_process.pid), signal.SIGINT)

    astrality_process.wait()
    assert astrality_process.returncode == 0

@pytest.mark.skipif('TRAVIS' not in os.environ, reason='Only run on CI')
def test_invocation_of_main_process():
    main(test=True)
