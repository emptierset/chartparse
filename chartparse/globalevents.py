"""For representing the data related to lyrics, sections, and more.

You should not need to create any of this module's objects manually; please instead create a
:class:`~chartparse.chart.Chart` and inspect its attributes via that object.

.. _Google Python Style Guide:
    http://google.github.io/styleguide/pyguide.html

"""

from __future__ import annotations

import dataclasses
import logging
import re
import typing as typ

import chartparse.track
from chartparse.event import Event
from chartparse.exceptions import RegexNotMatchError
from chartparse.tick import Tick
from chartparse.util import DictPropertiesEqMixin, DictReprMixin, DictReprTruncatedSequencesMixin

if typ.TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Iterable, Sequence

    from chartparse.sync import BPMEvents

logger = logging.getLogger(__name__)


@typ.final
@dataclasses.dataclass(frozen=True, kw_only=True)
class GlobalEventsTrack(DictPropertiesEqMixin, DictReprTruncatedSequencesMixin):
    """A :class:`~chartparse.chart.Chart`'s :class:`~chartparse.globalevents.GlobalEvent`\\ s.

    This is a ``frozen``, ``kw_only`` dataclass.
    """

    _Self = typ.TypeVar("_Self", bound="GlobalEventsTrack")

    section_name: typ.Final[str] = "Events"
    """The name of this track's section in a ``.chart`` file."""

    text_events: Sequence[TextEvent]
    """A ``GlobalEventTrack``'s ``TextEvent``\\ s."""

    section_events: Sequence[SectionEvent]
    """A ``GlobalEventTrack``'s ``SectionEvent``\\ s."""

    lyric_events: Sequence[LyricEvent]
    """A ``GlobalEventTrack``'s ``LyricEvent``\\ s."""

    @classmethod
    def from_chart_lines(
        cls: type[_Self],
        lines: Iterable[str],
        bpm_events: BPMEvents,
    ) -> _Self:
        """Initializes instance attributes by parsing an iterable of strings.

        Args:
            lines: An iterable of strings most likely from a Moonscraper ``.chart``.
            bpm_events: The chart's wrapped BPMEvents.

        Returns:
            A ``GlobalEventsTrack`` parsed from ``lines``.
        """

        text_data, section_data, lyric_data = cls._parse_data_from_chart_lines(lines)

        text_events = chartparse.track.build_events_from_data(
            text_data,
            TextEvent.from_parsed_data,
            bpm_events,
        )
        section_events = chartparse.track.build_events_from_data(
            section_data,
            SectionEvent.from_parsed_data,
            bpm_events,
        )
        lyric_events = chartparse.track.build_events_from_data(
            lyric_data,
            LyricEvent.from_parsed_data,
            bpm_events,
        )
        return cls(
            text_events=text_events,
            section_events=section_events,
            lyric_events=lyric_events,
        )

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


@dataclasses.dataclass(kw_only=True, frozen=True)
class GlobalEvent(Event):
    """An event in a :class:`~chartparse.globalevents.GlobalEventsTrack`.

    This is typically used only as a base class for more specialized subclasses. It implements an
    attractive ``__str__`` representation and supplies a regular expression template for subclasses
    to fill in.

    Subclasses should define ``_regex_prog`` and can be instantiated with their ``from_chart_line``
    method.

    This is a ``frozen``, ``kw_only`` dataclass.
    """

    _Self = typ.TypeVar("_Self", bound="GlobalEvent")

    value: str
    """The data that this event stores."""

    @classmethod
    def from_parsed_data(
        cls: type[_Self],
        data: GlobalEvent.ParsedData,
        prev_event: _Self | None,
        bpm_events: BPMEvents,
    ) -> _Self:
        """Obtain an instance of this object from parsed data.

        Args:
            data: The data necessary to create an event. Most likely from a Moonscraper ``.chart``.

            prev_event: The event of this type with the greatest ``tick`` value less than that of
                        this event. If this is ``None``, then this must be the first event of this
                        type.

            bpm_events: The chart's wrapped BPMEvents.

        Returns:
            An an instance of this object initialized from ``data``.
        """
        timestamp, proximal_bpm_event_index = bpm_events.timestamp_at_tick(
            data.tick,
            start_iteration_index=prev_event._proximal_bpm_event_index if prev_event else 0,
        )
        return cls(
            tick=data.tick,
            timestamp=timestamp,
            value=data.value,
            _proximal_bpm_event_index=proximal_bpm_event_index,
        )

    def __str__(self) -> str:
        to_join = [super().__str__()]
        to_join.append(f': "{self.value}"')
        return "".join(to_join)

    @dataclasses.dataclass(kw_only=True, frozen=True, repr=False)
    class ParsedData(Event.ParsedData, DictReprMixin):
        """The data on a single chart line associated with a ``GlobalEvent``.

        This is a ``frozen``, ``kw_only`` dataclass.
        """

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
            return cls(tick=Tick(int(raw_tick)), value=raw_value)


@typ.final
class TextEvent(GlobalEvent):
    """A :class:`~chartparse.globalevents.GlobalEvent` that stores freeform text event data."""

    @typ.final
    @dataclasses.dataclass(kw_only=True, frozen=True, repr=False)
    class ParsedData(GlobalEvent.ParsedData, DictReprMixin):
        """The data on a single chart line associated with a ``TextEvent``.

        This is a ``frozen``, ``kw_only`` dataclass.
        """

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
        """The data on a single chart line associated with a ``SectionEvent``.

        This is a ``frozen``, ``kw_only`` dataclass.
        """

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
        """The data on a single chart line associated with a ``LyricEvent``.

        This is a ``frozen``, ``kw_only`` dataclass.
        """

        _value_regex = "lyric (.*?)"
        _regex = GlobalEvent.ParsedData._regex_template.format(_value_regex)
        _regex_prog = re.compile(_regex)
