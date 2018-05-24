"""
Module for all event_listener classes.

Event listeners keep track of certain events for modules.
"""

import abc
import logging
import time
from collections import namedtuple
from datetime import datetime, timedelta
from math import inf
from typing import Dict, ClassVar, Tuple, Union, Optional

import pytz
from astral import AstralError, Location
from dateutil.tz import tzlocal


EventListenerConfig = Dict[str, Union[str, int, float, None]]
logger = logging.getLogger(__name__)


class EventListener(abc.ABC):
    """Class which defines different events."""

    type_: ClassVar[str]
    events: Tuple[str, ...]
    default_event_listener_config: EventListenerConfig

    def __init__(self, event_listener_config: EventListenerConfig) -> None:
        """Istantiate event listener based on the configuration of the user."""
        self.name = self.__class__.__name__.lower()

        # Use default values for event listener configuration options that are
        # not specified
        self.event_listener_config = self.default_event_listener_config.copy()
        self.event_listener_config.update(event_listener_config)

    def event(self) -> str:
        """
        Return the current determined event.

        If the event_listener option `force_event` is set, this value will
        always be returned instead of the correct event.
        """
        if self.event_listener_config.get('force_event', False):
            force_event = self.event_listener_config['force_event']

            if force_event not in self.events:
                logger.warning(
                    f'[event_listener/{self.name}] option `force_event` set to '
                    f'{force_event}, which is not a valid event type for '
                    f'the event_listener type "{self.name}": {self.events}.'
                    'Still using the option in case it is intentional.',
                )

            return force_event  # type: ignore

        return self._event()

    @abc.abstractmethod
    def _event(self) -> str:
        """Return the current determined event."""
        pass

    @abc.abstractmethod
    def time_until_next_event(self) -> timedelta:
        """Return the time remaining until the next event in seconds."""
        pass


class Solar(EventListener):
    """
    EventListener subclass which keeps track of the suns position in the sky.

    It changes event after dawn, sunrise, morning, afternoon, sunset, dusk.
    """

    type_ = 'solar'

    events: Tuple[str, ...] = (
        'sunrise',
        'morning',
        'afternoon',
        'sunset',
        'night',
    )
    default_event_listener_config = {
        'type': 'solar',
        'longitude': 0,
        'latitude': 0,
        'elevation': 0,
    }

    def __init__(self, event_listener_config: EventListenerConfig) -> None:
        """Initialize solar event listener object."""
        super().__init__(event_listener_config)
        self.location = self.construct_astral_location()

    def hardcoded_sun(
        self,
        date: Optional[datetime] = None,
    ) -> Dict[str, datetime]:
        """
        Return hardcoded sun when Astral cannot calculate all solar events.

        During summer, closer to the poles, the sun never dips properly below
        the horizon. In this case astral throws an AstralError, and we have
        to fall back to some hard coded defaults instead.

        :param date: Date used for solar events. Defaults to datetime.now().
        :return: Dict with event keys and datetime values.
        """
        if not date:
            date = datetime.now(tzlocal())

        d = date.replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )
        return {
            'dawn': d.replace(hour=5),
            'sunrise': d.replace(hour=6),
            'noon': d.replace(hour=12),
            'sunset': d.replace(hour=22),
            'dusk': d.replace(hour=23),
        }

    def _event(self) -> str:
        """Return the current, local solar event."""
        try:
            sun = self.location.sun()
            now = self.now()
        except AstralError:
            sun = self.hardcoded_sun()
            now = datetime.now(tzlocal())

        if now < sun['dawn']:
            event = 'night'
        elif now < sun['sunrise']:
            event = 'sunrise'
        elif now < sun['noon']:
            event = 'morning'
        elif now < sun['sunset']:
            event = 'afternoon'
        elif now < sun['dusk']:
            event = 'sunset'
        else:
            event = 'night'

        return event

    def time_until_next_event(self) -> timedelta:
        """Return timedelta until next solar event."""
        try:
            sun = self.location.sun()
            now = self.now()
        except AstralError:
            sun = self.hardcoded_sun()
            now = datetime.now(tzlocal())

        try:
            next_event = min(
                utc_time
                for utc_time
                in sun.values()
                if now < utc_time
            )
        except ValueError as exception:
            if str(exception) == 'min() arg is an empty sequence':
                # None of the solar events this current day are in the future,
                # so we need to compare with solar events tomorrow instead.
                tomorrow = now + timedelta(days=1, seconds=-1)
                try:
                    sun = self.location.sun(tomorrow)
                except AstralError:
                    sun = self.hardcoded_sun(tomorrow)

                next_event = min(
                    utc_time
                    for utc_time
                    in sun.values()
                    if now < utc_time
                )
            else:
                raise

        return next_event - now

    def now(self) -> datetime:
        """Return the current UTC time."""
        timezone = pytz.timezone('UTC')
        return timezone.localize(datetime.utcnow())

    def construct_astral_location(
        self,
    ) -> Location:
        """Return astral location object based on config."""
        # Initialize a custom location for astral, as it doesn't necessarily
        # include your current city of residence
        location = Location()

        # These two doesn't really matter
        location.name = 'CityNotImportant'
        location.region = 'RegionIsNotImportantEither'

        # But these are important, and should be provided by the user
        location.latitude = self.event_listener_config['latitude']
        location.longitude = self.event_listener_config['longitude']
        location.elevation = self.event_listener_config['elevation']
        location.timezone = 'UTC'

        return location


class Daylight(Solar):
    """Event listener keeping track of daylight at specific location."""

    type_ = 'daylight'

    events = ('day', 'night')
    default_event_listener_config = {
        'type': 'daylight',
        'longitude': 0,
        'latitude': 0,
        'elevation': 0,
    }

    def _event(self) -> str:
        """Return 'night' if the sun is below the horizon, else 'day'."""
        event = super()._event()
        if event == 'night':
            return 'night'
        else:
            return 'day'

    def time_until_next_event(self) -> timedelta:
        """Time left until daylight 'switches'."""
        event = self.event()
        now = self.now()

        if event == 'night':
            next_event = 'dawn'
        else:
            next_event = 'dusk'

        time_of_next_event = self.location.sun()[next_event]
        if time_of_next_event < now:
            tomorrow = now + timedelta(days=1, seconds=-1)
            time_of_next_event = self.location.sun(tomorrow)[next_event]

        return time_of_next_event - now


class Weekday(EventListener):
    """EventListener subclass which keeps track of the weekdays."""

    events = (
        'monday',
        'tuesday',
        'wednesday',
        'thursday',
        'friday',
        'saturday',
        'sunday',
    )
    default_event_listener_config = {'type': 'weekday'}
    type_ = 'weekday'

    weekdays = dict(zip(range(0, 7), events))

    @classmethod
    def _event(cls) -> str:
        """Return the current determined event."""
        return cls.weekdays[datetime.today().weekday()]

    def time_until_next_event(self) -> timedelta:
        """Return the time remaining until the next event in seconds."""
        tomorrow = datetime.today() + timedelta(days=1)
        tomorrow = tomorrow.replace(hour=0, minute=0)
        return tomorrow - datetime.now()


class Periodic(EventListener):
    """Constant frequency EventListener subclass."""

    type_ = 'periodic'

    class Events(tuple):
        """Helper class to check for valid event values."""

        def __contains__(self, item) -> bool:
            """Determine if event value is valid."""
            try:
                if float(item) - int(item) != 0:
                    # Not an integer
                    return False
                else:
                    # Check if item is positive
                    return 0 <= int(item) < inf
            except ValueError:
                # Not of valid type
                return False

    events = Events()
    default_event_listener_config = {
        'type': 'periodic',
        'seconds': 0,
        'minutes': 0,
        'hours': 0,
        'days': 0,
    }

    def __init__(self, event_listener_config: EventListenerConfig) -> None:
        """Initialize a constant frequency event listener."""
        super().__init__(event_listener_config)

        # Period specified by the user
        self.timedelta = timedelta(  # type: ignore
            seconds=self.event_listener_config['seconds'],
            minutes=self.event_listener_config['minutes'],
            hours=self.event_listener_config['hours'],
            days=self.event_listener_config['days'],
        )

        if self.timedelta.total_seconds() == 0.0:
            # If no period is specified by the user, then 1 hour is used
            self.timedelta = timedelta(hours=1)

        self.initialization_time = datetime.now()

    def _event(self) -> str:
        return str(int(
            (datetime.now() - self.initialization_time) / self.timedelta,
        ))

    def time_until_next_event(self) -> timedelta:
        """Return the time remaining until the next period in seconds."""
        return self.timedelta - \
            (datetime.now() - self.initialization_time) % self.timedelta


WorkDay = namedtuple('WorkDay', ('start', 'end'))


class TimeOfDay(EventListener):
    """
    EventListener which keeps track of time intervals each day of the week.

    The variable names used in the implementation, assumes that the 'on'
    events are referring to worktime.
    """

    events = ('on', 'off')
    default_event_listener_config = {
        'type': 'time_of_day',
        'monday': '09:00-17:00',
        'tuesday': '09:00-17:00',
        'wednesday': '09:00-17:00',
        'thursday': '09:00-17:00',
        'friday': '09:00-17:00',
        'saturday': '',
        'sunday': '',
    }
    type_ = 'time_of_day'

    def __init__(self, event_listener_config: EventListenerConfig) -> None:
        """Initialize time_of_day event listener based on config."""
        super().__init__(event_listener_config)
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
            work_period = self.event_listener_config[weekday_name]
            if not work_period:
                continue

            work_start, work_end = work_period.split('-')  # type: ignore
            workday = WorkDay(
                start=time.strptime(work_start, '%H:%M'),
                end=time.strptime(work_end, '%H:%M'),
            )
            self.workdays[weekday_name] = workday

    def _event(self) -> str:
        """Return the current determined period."""
        weekday_name = Weekday({'type': 'weekday'}).event()
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

    def time_until_next_event(self) -> timedelta:
        """Return the time remaining until the next event in seconds."""
        weekday_name = Weekday({'type': 'weekday'}).event()

        now = datetime.now()
        now_hour = now.hour
        now_minute = now.minute

        if self._event() == 'on':
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
                next_workday = self.workdays[
                    self.weekdays[next_workday_nums[0]]
                ]
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


class Static(EventListener):
    """EventListener subclass which never changes event."""

    events = ('static',)
    default_event_listener_config = {'type': 'static'}
    type_ = 'static'

    def _event(self) -> str:
        """Return the event 'static', as per specification."""
        return 'static'

    def time_until_next_event(self) -> timedelta:
        """Return a 100 year timedelta as an infinite approximation."""
        return timedelta(days=36500)


EVENT_LISTENERS = {
    'daylight': Daylight,
    'periodic': Periodic,
    'solar': Solar,
    'static': Static,
    'time_of_day': TimeOfDay,
    'weekday': Weekday,
}


def event_listener_factory(
    event_listener_config: EventListenerConfig,
) -> EventListener:
    """Return Class responsible for specific event listener `type`."""
    event_listener_type = event_listener_config['type']
    return EVENT_LISTENERS[event_listener_type](  # type: ignore
        event_listener_config,
    )
