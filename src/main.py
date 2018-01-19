import atexit
import os
import sys
import time

from config import user_configuration
from conky import exit_conky, initialize_conky, update_conky
from time_of_day import is_new_time_of_day, period_of_day
from wallpaper import exit_feh, update_wallpaper

atexit.register(exit_conky)
atexit.register(exit_feh)


def main() -> None:
    config = user_configuration()
    update_conky(config, period_of_day(config['location']['astral']))
    initialize_conky(config)

    changed = False
    period = 'not_set_yet'
    while True:
        changed, period = is_new_time_of_day(
            period,
            config['location']['astral'],
        )

        if changed:
            print('New time of day detected: ' + period)
            # We are in a new time of day, and we can change the background
            # image
            update_wallpaper(config, period)
            update_conky(config, period)

        time.sleep(int(config['behaviour']['refresh-period']))


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        exit_conky()
        exit_feh()
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
