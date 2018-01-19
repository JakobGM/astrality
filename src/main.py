import time

from config import user_configuration
from conky import update_conky
from time_of_day import is_new_time_of_day
from wallpaper import update_wallpaper

if __name__ == '__main__':
    config = user_configuration()

    changed = False
    period = 'not_set_yet'
    while True:
        changed, period = is_new_time_of_day(period, config['location']['astral'])

        if changed:
            print('New time of day detected: ' + period)
            # We are in a new time of day, and we can change the background
            # image
            update_wallpaper(config, period)

        time.sleep(int(config['behaviour']['refresh-period']))
