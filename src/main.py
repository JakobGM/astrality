import time

from config import user_configuration
from time_of_day import is_new_time_of_day
from wallpaper import update_wallpaper

if __name__ == '__main__':
    config = user_configuration()

    changed = False
    period = 'not_set_yet'
    while True:
        changed, period = is_new_time_of_day(period, config['location'])

        if changed:
            print('New time of day detected: ' + daytime)
            # We are in a new time of day, and we can change the background
            # image
            update_wallpaper(config, period)

        time.sleep(config['refresh_period'])
