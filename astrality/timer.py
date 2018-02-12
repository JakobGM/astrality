"""Module for all timer classes, keeping track of certain events for modules."""

import abc
from collections import namedtuple
import logging
import time
from datetime import datetime, timedelta
from math import inf
from typing import Dict, Tuple, Union

import pytz
from astral import Location


TimerConfig = Dict[str, Union[str, int, float, None]]
logger = logging.getLogger('astrality')


class Timer(abc.ABC):
    """Class which defines different periods."""

    periods: Tuple[str, ...]
    default_timer_config: TimerConfig

    def __init__(self, timer_config: TimerConfig) -> None:
        """Initialize a period timer based on the configuration of the user."""
        self.name = self.__class__.__name__.lower()

        # Use default values for timer configuration options that are not
        # specified
        self.timer_config = self.default_timer_config.copy()
        self.timer_config.update(timer_config)

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

            return force_period  # type: ignore

        return self._period()


    @abc.abstractmethod
    def _period(self) -> str:
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
    default_timer_config = {
        'type': 'solar',
        'longitude': 0,
        'latitude': 0,
        'elevation': 0,
    }

    def __init__(self, timer_config: TimerConfig) -> None:
        super().__init__(timer_config)
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
        location.latitude = self.timer_config['latitude']
        location.longitude = self.timer_config['longitude']
        location.elevation = self.timer_config['elevation']
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
    default_timer_config = {'type': 'weekday'}

    weekdays = dict(zip(range(0,7), periods))

    @classmethod
    def _period(cls) -> str:
        """Return the current determined period."""
        return cls.weekdays[datetime.today().weekday()]

    def time_until_next_period(self) -> timedelta:
        """Return the time remaining until the next period in seconds."""
        tomorrow = datetime.today() + timedelta(days=1)
        tomorrow = tomorrow.replace(hour=0, minute=0)
        return tomorrow - datetime.now()


class Periodic(Timer):
    """Constant frequency Timer subclass."""

    class Periods(tuple):
        def __contains__(self, item) -> bool:
            try:
                if float(item) - int(item) != 0:
                    return False
                else:
                    return 0 <= int(item) < inf
            except ValueError:
                return False

    periods = Periods()
    default_timer_config = {
        'type': 'periodic',
        'seconds': 0,
        'minutes': 0,
        'hours': 0,
        'days': 0,
    }

    def __init__(self, timer_config: TimerConfig) -> None:
        """Initialize a constant frequency timer."""

        super().__init__(timer_config)

        # Period specified by the user
        self.timedelta = timedelta(  # type: ignore
            seconds=self.timer_config['seconds'],
            minutes=self.timer_config['minutes'],
            hours=self.timer_config['hours'],
            days=self.timer_config['days'],
        )

        if self.timedelta.total_seconds() == 0.0:
            # If no period is specified by the user, then 1 hour is used
            self.timedelta = timedelta(hours=1)

        self.initialization_time = datetime.now()

    def _period(self) -> str:
        return str(int(
            (datetime.now() - self.initialization_time) / self.timedelta
        ))

    def time_until_next_period(self) -> timedelta:
        """Return the time remaining until the next period in seconds."""
        return self.timedelta - (datetime.now() - self.initialization_time) % self.timedelta


WorkDay = namedtuple('WorkDay', ('start', 'end',))

class TimeOfDay(Timer):
    """
    Timer which keeps track of time intervals each day of the week.

    The variable names used in the implementation, assumes that the 'on'
    periods are referring to worktime.
    """

    periods = ('on', 'off',)
    default_timer_config = {
        'type': 'time_of_day',
        'monday': '09:00-17:00',
        'tuesday': '09:00-17:00',
        'wednesday': '09:00-17:00',
        'thursday': '09:00-17:00',
        'friday': '09:00-17:00',
        'saturday': '',
        'sunday': '',
    }

    def __init__(self, timer_config: TimerConfig) -> None:
        super().__init__(timer_config)
        self.weekdays = (
            'monday',
            'tuesday',
            'wednesday',
            'thursday',
            'friday',
            'saturday',
            'sunday',
        )
        self.workdays: Dict[str, WorkDay] = {}

        for weekday_num, weekday_name in enumerate(self.weekdays):
            work_period = self.timer_config[weekday_name]
            if not work_period:
                continue

            work_start, work_end = work_period.split('-')  # type: ignore
            workday = WorkDay(
                start=time.strptime(work_start, '%H:%M'),
                end=time.strptime(work_end, '%H:%M'),
            )
            self.workdays[weekday_name] = workday

    def _period(self) -> str:
        """Return the current determined period."""
        weekday_name = Weekday({'type': 'weekday'}).period()
        if weekday_name not in self.workdays:
            return 'off'
        else:
            now = datetime.now()
            now_hour = now.hour
            now_minute = now.minute

            after_work_start = \
                now_hour >= self.workdays[weekday_name].start.tm_hour and \
                now_minute >= self.workdays[weekday_name].start.tm_min

            before_work_end = \
                now_hour <= self.workdays[weekday_name].end.tm_hour and \
                now_minute <= self.workdays[weekday_name].end.tm_min

            if after_work_start and before_work_end:
                return 'on'
            else:
                return 'off'


    def time_until_next_period(self) -> timedelta:
        """Return the time remaining until the next period in seconds."""
        weekday_name = Weekday({'type': 'weekday'}).period()

        now = datetime.now()
        now_hour = now.hour
        now_minute = now.minute

        if self._period() == 'on':
            # We are within work hours, and it is easy to find the work end for
            # the same day.
            return timedelta(
                hours=self.workdays[weekday_name].end.tm_hour - now_hour,
                minutes=self.workdays[weekday_name].end.tm_min - now_minute + 1,
            )

        else:
            # TODO: This is bad code, and should be done more cleanly in the
            #       future. But it works, and that is good enough for now.

            # The current zero-indexed weekday
            weekday_num = self.weekdays.index(weekday_name)

            # Get the zero indexed workdays
            workday_nums = tuple(
                self.weekdays.index(workday)
                for workday
                in self.workdays
            )

            # Retrieve all zero-indexed workdays that are later in this week
            next_workday_nums = tuple(
                workday_num
                for workday_num
                in workday_nums
                if workday_num > weekday_num
            )

            if len(next_workday_nums) > 0:
                days_until_next_workday = next_workday_nums[0] - weekday_num
                next_workday = self.workdays[self.weekdays[next_workday_nums[0]]]
            else:
                # There are no workdays later in this week, so we need to
                # get the *first* workday from next week instead.
                min_workday_num = min(workday_nums)
                days_until_next_workday = 7 + min_workday_num - weekday_num
                next_workday = self.workdays[self.weekdays[min_workday_num]]

            return timedelta(
                days=days_until_next_workday,
                hours=next_workday.start.tm_hour - now_hour,
                minutes=next_workday.start.tm_min - now_minute + 1,
            )


class Static(Timer):
    """Timer subclass which never changes period."""

    periods = ('static',)
    default_timer_config = {'type': 'static'}

    def _period(self) -> str:
        """Static timer asways returns the period 'static'."""

        return 'static'

    def time_until_next_period(self) -> timedelta:
        """Returns a 100 year timedelta as an infinite approximation."""

        return timedelta(days=36500)


TIMERS = {
        'solar': Solar,
        'weekday': Weekday,
        'periodic': Periodic,
        'static': Static,
}

def timer_factory(timer_config: Dict[str, Union[str, int]]) -> Timer:
    timer_type = timer_config['type']
    return TIMERS[timer_type](timer_config)  # type: ignore
