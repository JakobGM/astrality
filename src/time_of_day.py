import datetime
from typing import Tuple

from astral import Location
from tzlocal import get_localzone


PERIODS = ('sunrise', 'morning', 'afternoon', 'sunset', 'night')


def is_new_time_of_day(period: str, location: Location) -> Tuple[bool, str]:
    new_period = period_of_day(location)
    return new_period != period, new_period

def period_of_day(location: Location) -> str:
    timezone = get_localzone()
    now = timezone.localize(datetime.datetime.now())

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
