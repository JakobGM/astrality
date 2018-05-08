#!/usr/bin/env python3.6

"""The module meant to be run in order to start Astrality."""

import logging
import os
import signal
import subprocess
import sys
import time
from typing import Set, List

from astrality.config import user_configuration
from astrality.module import ModuleManager


logger = logging.getLogger(__name__)


def main(
    modules: List[str] = [],
    logging_level: str = 'INFO',
    dry_run: bool = False,
    test: bool = False,
):
    """
    Run the main process for Astrality.

    :param modules: Modules to be enabled. If empty, use astrality.yml.
    :param logging_level: Loging level.
    :param dry_run: If file system actions should be printed and skipped.
    :param test: If True, return after one iteration loop.
    """
    if 'ASTRALITY_LOGGING_LEVEL' in os.environ:
        # Override logging level if env variable is set
        logging_level = os.environ['ASTRALITY_LOGGING_LEVEL']

    # Set the logging level to the configured setting
    logging.basicConfig(level=logging_level)

    if not modules and not dry_run:
        # Quit old astrality instances
        kill_old_astrality_processes()

    # How to quit this process
    def exit_handler(signal=None, frame=None) -> None:
        """
        Cleanup all temporary files and run module exit handlers.

        The temp directory is left alone, for two reasons:
        1: An empty directory uses neglible disk space.
        2: If this process is interrupted by another Astrality instance,
           we might experience race conditions when the exit handler deletes
           the temporary directory *after* the new Astrality instance creates
           it.
        """
        logger.critical('Astrality was interrupted')
        logger.info('Cleaning up temporary files before exiting...')

        try:
            # Run all the module exit handlers
            module_manager.exit()
        except NameError:
            # The module_manager instance has not been assigned yet.
            pass

        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)

    # Some SIGINT signals are not properly interupted by python and converted
    # into KeyboardInterrupts, so we have to register a signal handler to
    # safeguard against such cases. This seems to be the case when conky is
    # launched as a subprocess, making it the process that receives the SIGINT
    # signal and not python. These signal handlers cause issues for \
    # NamedTemporaryFile.close() though, so they are only registrered when
    # we are not testing.
    if not test:
        signal.signal(signal.SIGINT, exit_handler)

        # Also catch kill-signkal from OS,
        # e.g. `kill $(pgrep -f "python astrality.py")`
        signal.signal(signal.SIGTERM, exit_handler)

    try:
        (
            config,
            module_configs,
            global_context,
            directory,
        ) = user_configuration()

        if modules:
            config['modules']['enabled_modules'] = [
                {'name': module_name}
                for module_name
                in modules
            ]

        # Delay further actions if configuration says so
        time.sleep(config['astrality']['startup_delay'])

        module_manager = ModuleManager(
            config=config,
            modules=module_configs,
            context=global_context,
            directory=directory,
            dry_run=dry_run,
        )
        module_manager.finish_tasks()

        while True:
            if module_manager.has_unfinished_tasks():
                # TODO: Log which new event which has been detected
                logger.info('New event detected.')
                module_manager.finish_tasks()
                logger.info(f'Event change routine finished.')

            if test or dry_run:
                logger.debug('Main loop interupted due to --dry-run.')
                return
            elif not module_manager.keep_running:
                logger.info(
                    'No more tasks to be performed. '
                    'Executing on_exit blocks.',
                )
                module_manager.exit()
                return
            else:
                logger.info(
                    f'Waiting {module_manager.time_until_next_event()} '
                    'until next event change and ensuing update.',
                )

                # Weird bug related to sleeping more than 10e7 seconds
                # on MacOS, causing OSError: Invalid Argument
                wait = module_manager.time_until_next_event().total_seconds()
                if wait >= 10e7:
                    wait = 10e7

                time.sleep(wait)

    except KeyboardInterrupt:  # pragma: no cover
        exit_handler()


def other_astrality_pids() -> Set[int]:
    """Return the process ids (PIDs) of any other Astrality instances."""
    # Get all processes instanciated from this file
    result = subprocess.Popen(
        ['pgrep', '-f', 'astrality'],
        stdout=subprocess.PIPE,
        universal_newlines=True,
    )
    pids = set(int(pid.strip()) for pid in result.stdout)

    # Return all the PIDs except for the PID of this process
    this_process_pid = os.getpid()
    return pids - set((this_process_pid,))


def kill_old_astrality_processes() -> None:
    """Kill all other instances of this script, to prevent duplicates."""
    pids = other_astrality_pids()
    failed_exits = 0
    for pid in pids:
        try:
            logger.info(f'Killing duplicate Astrality process with pid {pid}.')
            os.kill(pid, signal.SIGTERM)
        except OSError:
            logger.error(
                f'Could not kill old instance of astrality with pid {pid}.',
            )
            logger.error('Continuing anyway...')
            failed_exits += 1

    while len(other_astrality_pids()) > failed_exits:
        # Wait for all the processes to exit properly
        time.sleep(0.2)


if __name__ == '__main__':
    main()
