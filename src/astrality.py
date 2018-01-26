#/usr/bin/env python3

"""The module meant to be run in order to start Astrality."""

import logging
import os
import signal
from typing import Set
import subprocess
import sys
import time

from config import user_configuration
from conky import exit_conky, start_conky_process, compile_conky_templates
from wallpaper import exit_feh, update_wallpaper

logger = logging.getLogger('astrality')
logging.basicConfig(level=os.environ.get('ASTRALITY_LOGGING_LEVEL', 'WARNING'))

def main():
    """Run the main process for Astrality."""

    # Quit old astrality instances
    kill_old_astrality_process()

    # How to quit this process
    def exit_handler(signal=None, frame=None) -> None:
        logger.critical('Astrality was interrupted')
        logger.info('Cleaning up temporary files before exiting...')
        exit_conky(config)
        exit_feh(config)

        # Delete all temporary files manually, because if we delete the
        # temp directory, the TemporaryFile closer will raise an error
        # when it tries to delete itself when it goes out of scope
        for file in config['_runtime']['conky_temp_files'].values():
            file.close()

        # The temp directory is left alone, for two reasons:
        # 1: An empty directory uses neglible disk space.
        # 2: If this process is interrupted by another Astrality instance,
        #    we might experience race conditions when the exit handler deletes
        #    the temporary directory *after* the new Astrality instance creates it.

        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)

    # Some SIGINT signals are not properly interupted by python and converted
    # into KeyboardInterrupts, so we have to register a signal handler to
    # safeguard against such cases. This seems to be the case when conky is
    # launched as a subprocess, making it the process that receives the SIGINT
    # signal and not python.
    signal.signal(signal.SIGINT, exit_handler)

    # Also catch kill-signkal from OS, e.g. `kill $(pgrep -f "python astrality.py")`
    signal.signal(signal.SIGTERM, exit_handler)

    try:
        config = user_configuration()
        timer = config['_runtime']['timer_class'](config)
        old_period = timer.period()
        update_wallpaper(config, timer.period())

        # We might need to wait some time before starting conky, as startup
        # scripts may alter screen layouts and interfer with conky
        time.sleep(int(config['conky'].get('startup_delay', '0')))
        compile_conky_templates(config, timer.period())
        start_conky_process(config)

        while True:
            new_period = timer.period()
            changed = new_period != old_period

            if changed:
                logger.info('New time of day detected: ' + period)
                # We are in a new time of day, and we can change the background
                # image
                update_wallpaper(config, new_period)
                compile_conky_templates(config, new_period)
                old_period = new_period
                logger.info(f'Configuration updated.')

            logger.info(f'Waiting {timer.time_until_next_period()} seconds until next update.')
            time.sleep(timer.time_until_next_period())

    except KeyboardInterrupt:
        exit_handler()

def other_astrality_pids() -> Set[int]:
    """Return the process ids (PIDs) of any other Astrality instances."""

    # Get all processes instanciated from this file
    result = subprocess.Popen(
        ['pgrep', '-f', __file__],
        stdout=subprocess.PIPE,
        universal_newlines=True,
    )
    pids = set(int(pid.strip()) for pid in result.stdout)

    # Return all the PIDs except for the PID of this process
    this_process_pid = os.getpid()
    return pids - set((this_process_pid,))


def kill_old_astrality_process() -> None:
    """Kill all other instances of this script, to prevent duplicates."""

    pids = other_astrality_pids()
    failed_exits = 0
    for pid in pids:
        try:
            logger.info(f'Killing duplicate Astrality process with pid {pid}.')
            os.kill(pid, signal.SIGTERM)
        except OSError:
            logger.error(f'Could not kill old instance of astrality with pid {pid}.')
            logger.error('Continuing anyway...')
            failed_exits += 1

    while len(other_astrality_pids()) > failed_exits:
        # Wait for all the processes to exit properly
        time.sleep(0.2)


if __name__ == '__main__':
    main()
