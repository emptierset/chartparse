"""For representing the data related to lyrics, sections, and more.

You should not need to create any of this module's objects manually; please instead create a
:class:`~chartparse.chart.Chart` and inspect its attributes via that object.

.. _Google Python Style Guide:
    http://google.github.io/styleguide/pyguide.html

"""

from __future__ import annotations

import datetime
import logging
import re
import typing
from collections.abc import Callable, Iterable, Sequence
from typing import ClassVar, Final, Optional, Pattern, Type, TypeVar

import chartparse.track
from chartparse.datastructures import ImmutableSortedList
from chartparse.event import Event, TimestampAtTickSupporter
from chartparse.exceptions import RegexNotMatchError
from chartparse.util import DictPropertiesEqMixin, DictReprTruncatedSequencesMixin

GlobalEventsTrackT = TypeVar("GlobalEventsTrackT", bound="GlobalEventsTrack")

logger = logging.getLogger(__name__)


@typing.final
class GlobalEventsTrack(DictPropertiesEqMixin, DictReprTruncatedSequencesMixin):
    """A :class:`~chartparse.chart.Chart`'s :class:`~chartparse.globalevents.GlobalEvent`\\ s."""

    resolution: Final[int]
    """The number of ticks for which a quarter note lasts."""

    text_events: Final[Sequence[TextEvent]]
    """A ``GlobalEventTrack``'s ``TextEvent``\\ s."""

    section_events: Final[Sequence[SectionEvent]]
    """A ``GlobalEventTrack``'s ``SectionEvent``\\ s."""

    lyric_events: Final[Sequence[LyricEvent]]
    """A ``GlobalEventTrack``'s ``LyricEvent``\\ s."""

    section_name: Final[str] = "Events"
    """The name of this track's section in a ``.chart`` file."""

    def __init__(
        self,
        resolution: int,
        text_events: Sequence[TextEvent],
        section_events: Sequence[SectionEvent],
        lyric_events: Sequence[LyricEvent],
    ) -> None:
        """Instantiates all instance attributes."""

        if resolution <= 0:
            raise ValueError(f"resolution ({resolution}) must be positive")

        self.resolution = resolution
        self.text_events = text_events
        self.section_events = section_events
        self.lyric_events = lyric_events

    @classmethod
    def from_chart_lines(
        cls: Type[GlobalEventsTrackT],
        iterator_getter: Callable[[], Iterable[str]],
        tatter: TimestampAtTickSupporter,
    ) -> GlobalEventsTrackT:
        """Initializes instance attributes by parsing an iterable of strings.

        Args:
            iterator_getter: The iterable of strings returned by this is most likely from a
                Moonscraper ``.chart``. Must be a function so the strings can be iterated over
                multiple times, if necessary.
            tatter: An object that can be used to get a timestamp at a particular tick.

        Returns:
            A ``GlobalEventsTrack`` parsed from the strings returned by ``iterator_getter``.
        """

        text_events: ImmutableSortedList[
            TextEvent
        ] = chartparse.track.parse_events_from_chart_lines(
            iterator_getter(),
            TextEvent.from_chart_line,
            tatter,
        )
        section_events: ImmutableSortedList[
            SectionEvent
        ] = chartparse.track.parse_events_from_chart_lines(
            iterator_getter(),
            SectionEvent.from_chart_line,
            tatter,
        )
        lyric_events: ImmutableSortedList[
            LyricEvent
        ] = chartparse.track.parse_events_from_chart_lines(
            iterator_getter(),
            LyricEvent.from_chart_line,
            tatter,
        )
        return cls(tatter.resolution, text_events, section_events, lyric_events)


GlobalEventT = TypeVar("GlobalEventT", bound="GlobalEvent")


class GlobalEvent(Event):
    """An event in a :class:`~chartparse.globalevents.GlobalEventsTrack`.

    This is typically used only as a base class for more specialized subclasses. It implements an
    attractive ``__str__`` representation and supplies a regular expression template for subclasses
    to fill in.

    Subclasses should define ``_regex_prog`` and can be instantiated with their ``from_chart_line``
    method.
    """

    value: Final[str]
    """The data that this event stores."""

    _regex: ClassVar[str]
    _regex_prog: ClassVar[Pattern[str]]

    # Match 1: Tick
    # Match 2: Event value (to be added by subclass via template hole)
    _regex_template: Final[str] = r"^\s*?(\d+?) = E \"{}\"\s*?$"

    def __init__(
        self,
        tick: int,
        timestamp: datetime.timedelta,
        value: str,
        # TODO: Consider making proximal_bpm_event_index required.
        proximal_bpm_event_index: int = 0,
    ) -> None:
        super().__init__(tick, timestamp, proximal_bpm_event_index=proximal_bpm_event_index)
        self.value = value

    @classmethod
    def from_chart_line(
        cls: Type[GlobalEventT],
        line: str,
        prev_event: Optional[GlobalEventT],
        tatter: TimestampAtTickSupporter,
    ) -> GlobalEventT:
        """Attempt to obtain an instance of this object from a string.

        Args:
            line: Most likely a line from a Moonscraper ``.chart``.
            prev_event: The event
            tatter: An object that can be used to get a timestamp at a particular tick.

        Returns:
            An an instance of this object parsed from ``line``.

        Raises:
            RegexNotMatchError: If the mixed-into class' ``_regex`` does not match ``line``.
        """
        m = cls._regex_prog.match(line)
        if not m:
            raise RegexNotMatchError(cls._regex, line)
        tick, value = int(m.group(1)), m.group(2)
        timestamp, proximal_bpm_event_index = tatter.timestamp_at_tick(
            tick,
            proximal_bpm_event_index=prev_event._proximal_bpm_event_index if prev_event else 0,
        )
        return cls(tick, timestamp, value, proximal_bpm_event_index=proximal_bpm_event_index)

    def __str__(self) -> str:  # pragma: no cover
        to_join = [super().__str__()]
        to_join.append(f': "{self.value}"')
        return "".join(to_join)


@typing.final
class TextEvent(GlobalEvent):
    """A :class:`~chartparse.globalevents.GlobalEvent` that stores freeform text event data."""

    _regex = GlobalEvent._regex_template.format("([^ ]*?)")
    _regex_prog = re.compile(_regex)


@typing.final
class SectionEvent(GlobalEvent):
    """A :class:`~chartparse.globalevents.GlobalEvent` that signifies a new section.

    The event's ``value`` attribute contains the section's name.
    """

    _regex = GlobalEvent._regex_template.format("section (.*?)")
    _regex_prog = re.compile(_regex)


@typing.final
class LyricEvent(GlobalEvent):
    """A :class:`~chartparse.globalevents.GlobalEvent` that signifies a new section.

    The event's ``value`` attribute contains the lyric's text, typically a single syllable's worth.
    """

    _regex = GlobalEvent._regex_template.format("lyric (.*?)")
    _regex_prog = re.compile(_regex)
