import datetime
import pytz
from typing import Tuple

from astral import Location


PERIODS = ('sunrise', 'morning', 'afternoon', 'sunset', 'night')


def is_new_time_of_day(period: str, location: Location) -> Tuple[bool, str]:
    new_period = period_of_day(location)
    return new_period != period, new_period


def period_of_day(location: Location) -> str:
    timezone = pytz.timezone(location.timezone)
    now = timezone.localize(datetime.datetime.utcnow())

    if now < location.sun()['dawn']:
        period = 'night'
    elif now < location.sun()['sunrise']:
        period = 'sunrise'
    elif now < location.sun()['noon']:
        period = 'morning'
    elif now < location.sun()['sunset']:
        period = 'afternoon'
    elif now < location.sun()['dusk']:
        period = 'sunset'
    else:
        period = 'night'

    return period


def astral_location(
    latitude: float,
    longitude: float,
    elevation: float,
) -> Location:
    # Initialize a custom location for astral, as it doesn't necessarily include
    # your current city of residence
    location = Location()

    # These two doesn't really matter
    location.name = 'CityNotImportant'
    location.region = 'RegionIsNotImportantEither'

    # But these are important, and should be provided by the user
    location.latitude = latitude
    location.longitude = longitude
    location.elevation = elevation
    location.timezone = 'UTC'

    return location
