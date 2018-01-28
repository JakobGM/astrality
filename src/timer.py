import abc
from datetime import datetime, timedelta
from typing import Any, Dict, Tuple

import pytz
from astral import Location

from resolver import Resolver


class Timer(abc.ABC):
    """Class which defines different periods."""

    periods: Tuple[str, ...]

    @abc.abstractmethod
    def __init__(self, config: Resolver) -> None:
        """Initialize a period timer based on the configuration of the user."""
        pass

    @abc.abstractmethod
    def period(self) -> str:
        """Return the current determined period."""
        pass

    @abc.abstractmethod
    def time_until_next_period(self) -> timedelta:
        """Return the time remaining until the next period in seconds."""
        pass


class Solar(Timer):
    """
    Timer subclass which keeps track of the suns position in the sky.

    It changes period after dawn, sunrise, morning, afternoon, sunset, dusk.
    """
    periods = ('sunrise', 'morning', 'afternoon', 'sunset', 'night')

    def __init__(self, config: Resolver) -> None:
        self.config = config
        self.location = self.construct_astral_location()

    def period(self) -> str:
        now = self.now()

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

    def time_until_next_period(self) -> timedelta:
        now = self.now()
        try:
            next_period = min(
                utc_time
                for utc_time
                in self.location.sun().values()
                if now < utc_time
            )
        except ValueError as exception:
            if str(exception) == 'min() arg is an empty sequence':
                # None of the solar periods this current day are in the future,
                # so we need to compare with solar periods tomorrow instead.
                tomorrow = now + timedelta(days=1, seconds=-1)
                next_period = min(
                    utc_time
                    for utc_time
                    in self.location.sun(tomorrow).values()
                    if now < utc_time
                )
            else:
                raise RuntimeError('Could not find the time of the next period')

        return next_period - now

    def now(self) -> datetime:
        """Return the current UTC time."""
        timezone = pytz.timezone('UTC')
        return timezone.localize(datetime.utcnow())

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


class Weekday(Timer):
    """Timer subclass which keeps track of the weekdays."""

    periods = (
        'monday',
        'tuesday',
        'wednesday',
        'thursday',
        'friday',
        'saturday',
        'sunday',
    )

    weekdays = dict(zip(range(0,7), periods))

    def __init__(self, config: Resolver) -> None:
        """Initialize a weekday tracker independent of user configuration."""
        pass

    def period(self) -> str:
        """Return the current determined period."""
        return self.weekdays[datetime.today().weekday()]

    def time_until_next_period(self) -> timedelta:
        """Return the time remaining until the next period in seconds."""
        tomorrow = datetime.today() + timedelta(days=1)
        tomorrow = tomorrow.replace(hour=0, minute=0)
        return tomorrow - datetime.now()


TIMERS = {
        'solar': Solar,
        'weekday': Weekday,
}
