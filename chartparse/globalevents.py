"""For representing the data related to lyrics, sections, and more.

You should not need to create any of this module's objects manually; please instead create a
:class:`~chartparse.chart.Chart` and inspect its attributes via that object.

.. _Google Python Style Guide:
    http://google.github.io/styleguide/pyguide.html

"""

from __future__ import annotations

import dataclasses
import datetime
import logging
import re
import typing as typ
from collections.abc import Iterable, Sequence

import chartparse.track
from chartparse.event import Event, TimestampAtTickSupporter
from chartparse.exceptions import RegexNotMatchError
from chartparse.util import DictPropertiesEqMixin, DictReprMixin, DictReprTruncatedSequencesMixin

logger = logging.getLogger(__name__)


@typ.final
class GlobalEventsTrack(DictPropertiesEqMixin, DictReprTruncatedSequencesMixin):
    """A :class:`~chartparse.chart.Chart`'s :class:`~chartparse.globalevents.GlobalEvent`\\ s."""

    _Self = typ.TypeVar("_Self", bound="GlobalEventsTrack")

    resolution: typ.Final[int]
    """The number of ticks for which a quarter note lasts."""

    text_events: typ.Final[Sequence[TextEvent]]
    """A ``GlobalEventTrack``'s ``TextEvent``\\ s."""

    section_events: typ.Final[Sequence[SectionEvent]]
    """A ``GlobalEventTrack``'s ``SectionEvent``\\ s."""

    lyric_events: typ.Final[Sequence[LyricEvent]]
    """A ``GlobalEventTrack``'s ``LyricEvent``\\ s."""

    section_name: typ.Final[str] = "Events"
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
        cls: type[_Self],
        lines: Iterable[str],
        tatter: TimestampAtTickSupporter,
    ) -> _Self:
        """Initializes instance attributes by parsing an iterable of strings.

        Args:
            lines: An iterable of strings most likely from a Moonscraper ``.chart``.
            tatter: An object that can be used to get a timestamp at a particular tick.

        Returns:
            A ``GlobalEventsTrack`` parsed from ``lines``.
        """

        text_data, section_data, lyric_data = cls._parse_data_from_chart_lines(lines)

        text_events = chartparse.track.build_events_from_data(
            text_data,
            TextEvent.from_parsed_data,
            tatter,
        )
        section_events = chartparse.track.build_events_from_data(
            section_data,
            SectionEvent.from_parsed_data,
            tatter,
        )
        lyric_events = chartparse.track.build_events_from_data(
            lyric_data,
            LyricEvent.from_parsed_data,
            tatter,
        )
        return cls(tatter.resolution, text_events, section_events, lyric_events)

    @classmethod
    def _parse_data_from_chart_lines(
        cls: type[_Self],
        lines: Iterable[str],
    ) -> tuple[
        list[TextEvent.ParsedData],
        list[SectionEvent.ParsedData],
        list[LyricEvent.ParsedData],
    ]:
        parsed_data = chartparse.track.parse_data_from_chart_lines(
            (LyricEvent.ParsedData, SectionEvent.ParsedData, TextEvent.ParsedData),
            lines,
        )
        return (
            parsed_data[TextEvent.ParsedData],
            parsed_data[SectionEvent.ParsedData],
            parsed_data[LyricEvent.ParsedData],
        )


# TODO: Make this a dataclass (and all events...?).
class GlobalEvent(Event):
    """An event in a :class:`~chartparse.globalevents.GlobalEventsTrack`.

    This is typically used only as a base class for more specialized subclasses. It implements an
    attractive ``__str__`` representation and supplies a regular expression template for subclasses
    to fill in.

    Subclasses should define ``_regex_prog`` and can be instantiated with their ``from_chart_line``
    method.
    """

    _Self = typ.TypeVar("_Self", bound="GlobalEvent")

    value: typ.Final[str]
    """The data that this event stores."""

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
    def from_parsed_data(
        cls: type[_Self],
        data: GlobalEvent.ParsedData,
        prev_event: _Self | None,
        tatter: TimestampAtTickSupporter,
    ) -> _Self:
        """Obtain an instance of this object from parsed data.

        Args:
            data: The data necessary to create an event. Most likely from a Moonscraper ``.chart``.
            prev_event: The event of this type with the greatest ``tick`` value less than that of
                this event. If this is ``None``, then this must be the first event of this type.
            tatter: An object that can be used to get a timestamp at a particular tick.

        Returns:
            An an instance of this object initialized from ``data``.
        """
        timestamp, proximal_bpm_event_index = tatter.timestamp_at_tick(
            data.tick,
            proximal_bpm_event_index=prev_event._proximal_bpm_event_index if prev_event else 0,
        )
        return cls(
            data.tick, timestamp, data.value, proximal_bpm_event_index=proximal_bpm_event_index
        )

    def __str__(self) -> str:  # pragma: no cover
        to_join = [super().__str__()]
        to_join.append(f': "{self.value}"')
        return "".join(to_join)

    @dataclasses.dataclass(kw_only=True, frozen=True, repr=False)
    class ParsedData(Event.ParsedData, DictReprMixin):
        _Self = typ.TypeVar("_Self", bound="GlobalEvent.ParsedData")

        value: str

        _regex: typ.ClassVar[str]
        _regex_prog: typ.ClassVar[typ.Pattern[str]]

        # Match 1: Tick
        # Match 2: Event value (to be added by subclass via _value_regex)
        _regex_template: typ.Final[str] = r"^\s*?(\d+?) = E \"{}\"\s*?$"
        _value_regex: typ.ClassVar[str]

        @classmethod
        def from_chart_line(cls: type[_Self], line: str) -> _Self:
            """Attempt to construct this object from a ``.chart`` line.

            Args:
                line: A string, most likely from a Moonscraper ``.chart``.

            Returns:
                An an instance of this object initialized from ``line``.

            Raises:
                RegexNotMatchError: If the mixed-into class' ``_regex`` does not match ``line``.
            """
            m = cls._regex_prog.match(line)
            if not m:
                raise RegexNotMatchError(cls._regex, line)
            raw_tick, raw_value = m.groups()
            return cls(tick=int(raw_tick), value=raw_value)


@typ.final
class TextEvent(GlobalEvent):
    """A :class:`~chartparse.globalevents.GlobalEvent` that stores freeform text event data."""

    @typ.final
    @dataclasses.dataclass(kw_only=True, frozen=True, repr=False)
    class ParsedData(GlobalEvent.ParsedData, DictReprMixin):
        _value_regex = r"([^ ]*?)"
        _regex = GlobalEvent.ParsedData._regex_template.format(_value_regex)
        _regex_prog = re.compile(_regex)


@typ.final
class SectionEvent(GlobalEvent):
    """A :class:`~chartparse.globalevents.GlobalEvent` that signifies a new section.

    The event's ``value`` attribute contains the section's name.
    """

    @typ.final
    @dataclasses.dataclass(kw_only=True, frozen=True, repr=False)
    class ParsedData(GlobalEvent.ParsedData, DictReprMixin):
        _value_regex = r"section (.*?)"
        _regex = GlobalEvent.ParsedData._regex_template.format(_value_regex)
        _regex_prog = re.compile(_regex)


@typ.final
class LyricEvent(GlobalEvent):
    """A :class:`~chartparse.globalevents.GlobalEvent` that signifies a new section.

    The event's ``value`` attribute contains the lyric's text, typically a single syllable's worth.
    """

    @typ.final
    @dataclasses.dataclass(kw_only=True, frozen=True, repr=False)
    class ParsedData(GlobalEvent.ParsedData, DictReprMixin):
        _value_regex = "lyric (.*?)"
        _regex = GlobalEvent.ParsedData._regex_template.format(_value_regex)
        _regex_prog = re.compile(_regex)
