import os
import signal
import shutil
import sys
import time

from config import Config, user_configuration
from conky import exit_conky, start_conky_process, compile_conky_templates
from timer import Solar
from wallpaper import exit_feh, update_wallpaper

def exit_handler(signal=None, frame=None):
    print('Solarity was interrupted')
    print('Cleaning up temporary files before exiting...')
    exit_conky(config)
    exit_feh(config)

    # Delete all temporary files manually, because if we delete the
    # temp directory, the TemporaryFile closer will raise an error
    # when it tries to delete itself when it goes out of scope
    for file in config['conky_temp_files'].values():
        file.close()

    # Now we can safely delete the temporary directory
    shutil.rmtree(config['temp_directory'])

    try:
        sys.exit(0)
    except SystemExit:
        os._exit(0)


if __name__ == '__main__':
    # Some SIGINT signals are not properly interupted by python and converted
    # into KeyboardInterrupts, so we have to register a signal handler to
    # safeguard against such cases. This seems to be the case when conky is
    # launched as a subprocess, making it the process that receives the SIGINT
    # signal and not python.
    signal.signal(signal.SIGINT, exit_handler)

    # Also catch kill-signkal from OS, e.g. `kill $(pgrep -f "python solarity.py")`
    signal.signal(signal.SIGTERM, exit_handler)

    try:
        config = user_configuration()
        timer = config['timer_class'](config)
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
                print('New time of day detected: ' + period)
                # We are in a new time of day, and we can change the background
                # image
                update_wallpaper(config, new_period)
                compile_conky_templates(config, new_period)
                old_period = new_period
                print(f'Configuration updated.')

            print(f'Waiting {timer.time_until_next_period()} seconds until next update.')
            time.sleep(timer.time_until_next_period())

    except KeyboardInterrupt:
        exit_handler()
