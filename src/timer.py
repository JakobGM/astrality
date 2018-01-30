import abc
from datetime import datetime, timedelta
import logging
from typing import Any, Dict, Tuple

import pytz
from astral import Location

from resolver import Resolver

logger = logging.getLogger('astrality')


class Timer(abc.ABC):
    """Class which defines different periods."""

    periods: Tuple[str, ...]

    def __init__(self, config: Resolver) -> None:
        """Initialize a period timer based on the configuration of the user."""
        self.name = self.__class__.__name__.lower()
        self.application_config = config
        self.timer_config = self.application_config.get(
            'timer/' + self.name,
            {},
        )

    def period(self) -> str:
        """
        Return the current determined period.

        If the timer option `force_period` is set, this value will always be
        returned instead of the correct period.
        """
        if self.timer_config.get('force_period', False):
            force_period = self.timer_config['force_period']

            if not force_period in self.periods:
                logger.warning(
                    f'[timer/{self.name}] option `force_period` set to '
                    f'{force_period}, which is not a valid period type for '
                    f'the timer type "{self.name}": {self.periods}. Still using'
                    ' the option in case it is intentional.'
                )

            return force_period

        return self._period()


    @abc.abstractmethod
    def _period(self) -> str:
        """Return the current determined period."""
        pass

    @abc.abstractmethod
    def time_until_next_period(self) -> timedelta:
        """Return the time remaining until the next period in seconds."""
        pass

    @property
    def config(self):
        return self.application_config.get('timer/' + self.name, {})


class Solar(Timer):
    """
    Timer subclass which keeps track of the suns position in the sky.

    It changes period after dawn, sunrise, morning, afternoon, sunset, dusk.
    """
    periods = ('sunrise', 'morning', 'afternoon', 'sunset', 'night')

    def __init__(self, config: Resolver) -> None:
        Timer.__init__(self, config)
        self.location = self.construct_astral_location()

    def _period(self) -> str:
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
        location.latitude = float(self.config.get('latitude', '0'))
        location.longitude = float(self.config.get('longitude', '0'))
        location.elevation = float(self.config.get('elevation', '0'))
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

    def _period(self) -> str:
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
