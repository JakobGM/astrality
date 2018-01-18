from configparser import ConfigParser
import datetime
import os
import time
from typing import Dict, Tuple

from astral import Location
from tzlocal import get_localzone

PERIODS = ('sunrise', 'morning', 'afternoon', 'sunset', 'night')
Config = ConfigParser

def user_configuration() -> Config:
    config = ConfigParser()
    config.read('solarity.conf')

    config_dir = os.getenv('XDG_CONFIG_HOME', '~/.config')
    config['FileSystem'] = {'ConfigDirectory': config_dir + '/solarity'}

    return config

def astral_location(config: Config) -> Location:
    # Initialize a custom location for astral, as it doesn't necessarily include
    # your current city of residence
    location = Location()

    # These two doesn't really matter
    location.name = 'CityNotImportant'
    location.region = 'RegionIsNotImportantEither'

    # But these are important, and should be provided by the user
    location.latitude = float(config['Location']['Latitude'])
    location.longitude = float(config['Location']['Longitude'])
    location.elevation = float(config['Location']['Elevation'])

    # We can get the timezone from the system
    location.timezone = str(get_localzone())

    return location

def wallpaper_paths(config: Config) -> Dict[str, str]:
    wallpaper_theme = config['Themes']['WallpaperTheme']
    config_dir = config['FileSystem']['ConfigDirectory']
    wallpaper_directory = config_dir + '/wallpaper_themes/' + wallpaper_theme

    paths = {
        time_of_day: wallpaper_directory + '/' + time_of_day + '.jpg'
        for time_of_day
        in PERIODS
    }
    return paths


def is_new_time_of_day(daytime: str, location: Location) -> Tuple[bool, str]:
    changed = False
    now = datetime.datetime.now()

    if now.hour < location.sun()['dawn'].hour and daytime != 'night':
        daytime = 'night'
        changed = True

    elif now.hour < location.sun()['sunrise'].hour and daytime != 'sunrise':
        daytime = 'sunrise'
        changed = True

    elif now.hour < location.sun()['noon'].hour and daytime != 'morning':
        daytime = 'morning'
        changed = True

    elif now.hour < location.sun()['sunset'].hour and daytime != 'afternoon':
        daytime = 'afternoon'
        changed = True

    elif now.hour < location.sun()['dusk'].hour and daytime != 'sunset':
        daytime = 'sunset'
        changed = True

    elif daytime != 'night':
        daytime = 'night'
        changed = True

    return changed, daytime


def update_wallpaper(wallpaper_paths: Dict[str, str], daytime: str) -> None:
    wallpaper_path = wallpaper_paths[daytime]

    print('Setting new wallpaper: ' + wallpaper_path)
    os.system('feh --bg-scale ' + wallpaper_path)


def update_conky(conky_paths: Dict[str, str]) -> None:
    if daytime == 'night':
        os.system('sed -i "s/282828/CBCDFF/g" $XDG_CONFIG_HOME/conky/*.conf')
    else:
        os.system('sed -i "s/CBCDFF/282828/g" $XDG_CONFIG_HOME/conky/*.conf')



if __name__ == '__main__':
    daytime = 'not_set_yet'
    changed = False

    config = user_configuration()
    location = astral_location(config)
    wallpapers = wallpaper_paths(config)

    refresh_period = int(config['Behaviour'].get('RefreshPeriod', '60'))

    while True:
        changed, daytime = is_new_time_of_day(daytime, location)

        if changed:
            print('New time of day detected: ' + daytime)
            # We are in a new time of day, and we can change the background image
            update_wallpaper(wallpapers, daytime)

        time.sleep(refresh_period)
