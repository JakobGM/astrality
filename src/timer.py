import abc
import datetime
from typing import Any, Dict, Tuple

import pytz
from astral import Location

Config = Dict[str, Any]


class Timer(abc.ABC):
    """Class which defines different periods."""

    periods = Tuple[str]

    @abc.abstractmethod
    def __init__(self, config: Config) -> None:
        """Initialize a period timer based on the configuration of the user."""
        pass

    @abc.abstractmethod
    def period(self) -> str:
        """Return the current determined period."""
        pass


class Solar(Timer):
    """
    Timer subclass which keeps track of the suns position in the sky.

    It changes period after dawn, sunrise, morning, afternoon, sunset, dusk.
    """
    periods = ('sunrise', 'morning', 'afternoon', 'sunset', 'night')

    def __init__(self, config: Config) -> None:
        self.config = config
        self.location = self.construct_astral_location()

    def period(self) -> str:
        timezone = pytz.timezone(self.location.timezone)
        now = timezone.localize(datetime.datetime.utcnow())

        if now < self.location.sun()['dawn']:
            period = 'night'
        elif now < self.location.sun()['sunrise']:
            period = 'sunrise'
        elif now < self.location.sun()['noon']:
            period = 'morning'
        elif now < self.location.sun()['sunset']:
            period = 'afternoon'
        elif now < self.location.sun()['dusk']:
            period = 'sunset'
        else:
            period = 'night'

        return period

    def construct_astral_location(
        self,
    ) -> Location:
        # Initialize a custom location for astral, as it doesn't necessarily include
        # your current city of residence
        location = Location()

        # These two doesn't really matter
        location.name = 'CityNotImportant'
        location.region = 'RegionIsNotImportantEither'

        # But these are important, and should be provided by the user
        location.latitude = float(self.config['location']['latitude'])
        location.longitude = float(self.config['location']['longitude'])
        location.elevation = float(self.config['location']['elevation'])
        location.timezone = 'UTC'

        return location
