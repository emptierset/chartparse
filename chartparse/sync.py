"""For representing the data related to tempo and meter.

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

import chartparse.tick
import chartparse.track
from chartparse.event import Event, TimestampAtTickSupporter
from chartparse.exceptions import RegexNotMatchError
from chartparse.util import DictPropertiesEqMixin, DictReprMixin, DictReprTruncatedSequencesMixin

if typ.TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Iterable, Sequence

logger = logging.getLogger(__name__)


@typ.final
@dataclasses.dataclass(frozen=True, kw_only=True)
class SyncTrack(DictPropertiesEqMixin, DictReprTruncatedSequencesMixin):
    """All of a :class:`~chartparse.chart.Chart` object's tempo-mapping related events.

    This is a ``frozen``, ``kw_only`` dataclass.
    """

    _Self = typ.TypeVar("_Self", bound="SyncTrack")

    resolution: int
    """The number of ticks for which a quarter note lasts."""

    time_signature_events: Sequence[TimeSignatureEvent]
    """A ``SyncTrack``'s ``TimeSignatureEvent``\\ s."""

    bpm_events: Sequence[BPMEvent]
    """A ``SyncTrack``'s ``BPMEvent``\\ s."""

    anchor_events: Sequence[AnchorEvent]
    """A ``SyncTrack``'s ``AnchorEvent``\\ s."""

    section_name: typ.ClassVar[str] = "SyncTrack"
    """The name of this track's section in a ``.chart`` file."""

    def __post_init__(self):
        """Validates all instance attributes.

        Raises:
            ValueError: If ``time_signature_events`` or ``bpm_events`` is empty, or if either of
                their first elements has a ``tick`` value of ``0``.
        """
        if self.resolution <= 0:
            raise ValueError(f"resolution ({self.resolution}) must be positive")
        if not self.time_signature_events:
            raise ValueError("time_signature_events must not be empty")
        if self.time_signature_events[0].tick != 0:
            raise ValueError(
                f"first TimeSignatureEvent {self.time_signature_events[0]} must have tick 0"
            )
        if not self.bpm_events:
            raise ValueError("bpm_events must not be empty")
        if self.bpm_events[0].tick != 0:
            raise ValueError(f"first BPMEvent {self.bpm_events[0]} must have tick 0")

    @classmethod
    def from_chart_lines(
        cls: type[_Self],
        resolution: int,
        lines: Iterable[str],
    ) -> _Self:
        """Initializes instance attributes by parsing an iterable of strings.

        Args:
            resolution: The number of ticks in a quarter note.
            lines: An iterable of strings most likely from a Moonscraper ``.chart``.

        Returns:
            A ``SyncTrack`` parsed from ``lines``.
        """

        time_signature_data, bpm_data, anchor_data = cls._parse_data_from_chart_lines(lines)

        bpm_events = chartparse.track.build_events_from_data(
            bpm_data,
            BPMEvent.from_parsed_data,
            resolution,
        )

        @dataclasses.dataclass(frozen=True, kw_only=True)
        class _TimestampAtTicker(object):
            resolution: int

            def timestamp_at_tick(
                self, tick: int, proximal_bpm_event_index: int = 0
            ) -> tuple[datetime.timedelta, int]:
                return cls._timestamp_at_tick(
                    bpm_events, tick, self.resolution, proximal_bpm_event_index
                )  # pragma: no cover

        tatter = _TimestampAtTicker(resolution=resolution)

        time_signature_events = chartparse.track.build_events_from_data(
            time_signature_data, TimeSignatureEvent.from_parsed_data, tatter
        )

        anchor_events = chartparse.track.build_events_from_data(
            anchor_data, AnchorEvent.from_parsed_data
        )

        return cls(
            resolution=resolution,
            time_signature_events=time_signature_events,
            bpm_events=bpm_events,
            anchor_events=anchor_events,
        )

    @classmethod
    def _parse_data_from_chart_lines(
        cls: type[_Self],
        lines: Iterable[str],
    ) -> tuple[
        list[TimeSignatureEvent.ParsedData],
        list[BPMEvent.ParsedData],
        list[AnchorEvent.ParsedData],
    ]:
        parsed_data = chartparse.track.parse_data_from_chart_lines(
            (BPMEvent.ParsedData, TimeSignatureEvent.ParsedData, AnchorEvent.ParsedData), lines
        )
        return (
            parsed_data[TimeSignatureEvent.ParsedData],
            parsed_data[BPMEvent.ParsedData],
            parsed_data[AnchorEvent.ParsedData],
        )

    def timestamp_at_tick(
        self, tick: int, proximal_bpm_event_index: int = 0
    ) -> tuple[datetime.timedelta, int]:
        """Returns the timestamp at the input tick.

        Args:
            tick: The tick at which the timestamp should be calculated.

        Kwargs:
            proximal_bpm_event_index: An optional optimizing input that allows this function to
                start iterating over ``BPMEvent``s at a later index. Only pass this if you are
                certain that the event that should be proximal to ``tick`` is _not_ before this
                index.

        Returns:
            The timestamp at the input tick, plus the index of the ``BPMEvent`` proximal to the
            input tick. This index can be passed to successive calls to this function via
            ``proximal_bpm_event_index`` as an optimization.
        """
        return self._timestamp_at_tick(
            self.bpm_events,
            tick,
            self.resolution,
            proximal_bpm_event_index=proximal_bpm_event_index,
        )

    # TODO: This method only needs to exist because we need to be able to use timestamp_at_tick
    # during from_chart_lines, and we don't yet have the object we need for it. If we factor out
    # bpm_events to its own object, it can own timestamp_at_tick.
    @staticmethod
    def _timestamp_at_tick(
        bpm_events: Sequence[BPMEvent],
        tick: int,
        resolution: int,
        proximal_bpm_event_index: int = 0,
    ) -> tuple[datetime.timedelta, int]:
        """Allows ``timestamp_at_tick`` to be used by injecting a ``bpm_events`` object."""

        proximal_bpm_event_index = SyncTrack._index_of_proximal_bpm_event(
            bpm_events, tick, proximal_bpm_event_index=proximal_bpm_event_index
        )
        proximal_bpm_event = bpm_events[proximal_bpm_event_index]
        ticks_since_proximal_bpm_event = tick - proximal_bpm_event.tick
        seconds_since_proximal_bpm_event = chartparse.tick.seconds_from_ticks_at_bpm(
            ticks_since_proximal_bpm_event,
            proximal_bpm_event.bpm,
            resolution,
        )
        timedelta_since_proximal_bpm_event = datetime.timedelta(
            seconds=seconds_since_proximal_bpm_event
        )
        timestamp = proximal_bpm_event.timestamp + timedelta_since_proximal_bpm_event
        return timestamp, proximal_bpm_event_index

    @staticmethod
    def _index_of_proximal_bpm_event(
        bpm_events: Sequence[BPMEvent], tick: int, proximal_bpm_event_index: int = 0
    ) -> int:
        if not bpm_events:
            raise ValueError("bpm_events must not be empty")

        index_of_last_event = len(bpm_events) - 1
        if proximal_bpm_event_index > index_of_last_event:
            raise ValueError(
                f"there are no BPMEvents at or after index {proximal_bpm_event_index} in "
                "bpm_events"
            )

        first_event = bpm_events[proximal_bpm_event_index]
        if first_event.tick > tick:
            raise ValueError(
                f"input tick {tick} precedes tick value of first BPMEvent ({first_event.tick})"
            )

        # Do NOT iterate over last BPMEvent, since it has no next event.
        for index in range(proximal_bpm_event_index, index_of_last_event):
            if bpm_events[index + 1].tick > tick:
                return index

        # If none of the previous BPMEvents are proximal, the last event is proximal by
        # definition.
        return index_of_last_event


@typ.final
@dataclasses.dataclass(kw_only=True, frozen=True)
class TimeSignatureEvent(Event):
    """An event representing a time signature change at a particular tick.

    This is a ``frozen``, ``kw_only`` dataclass.
    """

    _Self = typ.TypeVar("_Self", bound="TimeSignatureEvent")

    upper_numeral: int
    """The number indicating how many beats constitute a bar."""

    lower_numeral: int
    """The number indicating the note value that represents one beat."""

    _default_lower_numeral: typ.ClassVar[int] = 4

    @classmethod
    def from_parsed_data(
        cls: type[_Self],
        data: TimeSignatureEvent.ParsedData,
        prev_event: _Self | None,
        tatter: TimestampAtTickSupporter,
    ) -> _Self:
        """Obtain an instance of this object from parsed data.

        Args:
            data: The data necessary to create an event. Most likely from a Moonscraper ``.chart``.
            prev_event: The ``TimeSignatureEvent`` with the greatest ``tick`` value less than that
                of this event. If this is ``None``, then this must be the first
                ``TimeSignatureEvent``.
            tatter: An object that can be used to get a timestamp at a particular tick.

        Returns:
            An an instance of this object initialized from ``data``.
        """

        # The lower number is written by Moonscraper as the log2 of the true value.
        lower_numeral = 2**data.lower if data.lower is not None else cls._default_lower_numeral
        timestamp, proximal_bpm_event_index = tatter.timestamp_at_tick(
            data.tick,
            proximal_bpm_event_index=prev_event._proximal_bpm_event_index if prev_event else 0,
        )
        return cls(
            tick=data.tick,
            timestamp=timestamp,
            upper_numeral=data.upper,
            lower_numeral=lower_numeral,
            _proximal_bpm_event_index=proximal_bpm_event_index,
        )

    def __str__(self) -> str:  # pragma: no cover
        to_join = [super().__str__()]
        to_join.append(f": {self.upper_numeral}/{self.lower_numeral}")
        return "".join(to_join)

    @typ.final
    @dataclasses.dataclass(kw_only=True, frozen=True, repr=False)
    class ParsedData(Event.ParsedData, DictReprMixin):
        """The data on a single chart line associated with a ``TimeSignatureEvent``.

        This is a ``frozen``, ``kw_only`` dataclass.
        """

        _Self = typ.TypeVar("_Self", bound="TimeSignatureEvent.ParsedData")

        upper: int
        lower: int | None

        # Match 1: Tick
        # Match 2: Upper numeral
        # Match 3: Lower numeral (optional; assumed to be 4 if absent)
        _regex: typ.Final[str] = r"^\s*?(\d+?) = TS (\d+?)(?: (\d+?))?\s*?$"
        _regex_prog: typ.Final[typ.Pattern[str]] = re.compile(_regex)

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
            raw_tick, raw_upper, raw_lower = m.groups()
            try:
                lower = int(raw_lower)
            except TypeError:
                lower = None
            return cls(tick=int(raw_tick), upper=int(raw_upper), lower=lower)


@typ.final
@dataclasses.dataclass(kw_only=True, frozen=True)
class BPMEvent(Event):
    """An event representing a BPM (beats per minute) change at a particular tick.

    This is a ``frozen``, ``kw_only`` dataclass.
    """

    _Self = typ.TypeVar("_Self", bound="BPMEvent")

    bpm: float
    """The beats per minute value. Must not have more than 3 decimal places."""

    def __post_init__(self):
        """Validate instance attributes.

        Raises:
            ValueError: If ``bpm`` has more than 3 decimal places.
        """
        if round(self.bpm, 3) != self.bpm:
            raise ValueError(f"bpm {self.bpm} must not have more than 3 decimal places.")

    @classmethod
    def from_parsed_data(
        cls: type[_Self],
        data: BPMEvent.ParsedData,
        prev_event: _Self | None,
        resolution: int,
    ) -> _Self:
        """Obtain an instance of this object from parsed data.

        Args:
            data: The data necessary to create an event. Most likely from a Moonscraper ``.chart``.
            prev_event: The event of this type with the greatest ``tick`` value less than that of
                this event. If this is ``None``, then this must be the first event of this type.
            resolution: The number of ticks for which a quarter note lasts.

        Returns:
            An an instance of this object initialized from ``data``.

        Raises:
            ValueError: If ``prev_event.tick`` is not less than the tick value parsed from
                ``line``.
        """

        bpm_whole_part_str, bpm_decimal_part_str = data.raw_bpm[:-3], data.raw_bpm[-3:]
        bpm_whole_part = int(bpm_whole_part_str) if bpm_whole_part_str != "" else 0
        bpm_decimal_part = int(bpm_decimal_part_str) / 1000
        bpm = bpm_whole_part + bpm_decimal_part

        class TimestampAtTicker(object):
            resolution: typ.Final[int]

            def __init__(self, resolution: int):
                self.resolution = resolution

            def timestamp_at_tick(
                self, tick: int, proximal_bpm_event_index: int = 0
            ) -> tuple[datetime.timedelta, int]:
                if prev_event is None:
                    return datetime.timedelta(0), 0
                if tick <= prev_event.tick:
                    raise ValueError(
                        f"{cls.__name__} at tick {tick} does not occur after previous "
                        f"{cls.__name__} at tick {prev_event.tick}; tick values of "
                        f"{cls.__name__} must be strictly increasing."
                    )
                ticks_since_prev = tick - prev_event.tick
                seconds_since_prev = chartparse.tick.seconds_from_ticks_at_bpm(
                    ticks_since_prev, prev_event.bpm, self.resolution
                )
                timestamp = prev_event.timestamp + datetime.timedelta(seconds=seconds_since_prev)
                return timestamp, proximal_bpm_event_index

        tatter = TimestampAtTicker(resolution)
        timestamp, proximal_bpm_event_index = tatter.timestamp_at_tick(
            data.tick,
            proximal_bpm_event_index=prev_event._proximal_bpm_event_index if prev_event else 0,
        )
        return cls(
            tick=data.tick,
            timestamp=timestamp,
            bpm=bpm,
            _proximal_bpm_event_index=proximal_bpm_event_index,
        )

    def __str__(self) -> str:  # pragma: no cover
        to_join = [super().__str__()]
        to_join.append(f": {self.bpm} BPM")
        return "".join(to_join)

    @typ.final
    @dataclasses.dataclass(kw_only=True, frozen=True, repr=False)
    class ParsedData(Event.ParsedData, DictReprMixin):
        """The data on a single chart line associated with a ``BPMEvent``.

        This is a ``frozen``, ``kw_only`` dataclass.
        """

        _Self = typ.TypeVar("_Self", bound="BPMEvent.ParsedData")

        raw_bpm: str

        # Match 1: Tick
        # Match 2: BPM (the last 3 digits are the decimal places)
        _regex: typ.Final[str] = r"^\s*?(\d+?) = B (\d+?)\s*?$"
        _regex_prog: typ.Final[typ.Pattern[str]] = re.compile(_regex)

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
            raw_tick, raw_bpm = m.groups()
            return cls(tick=int(raw_tick), raw_bpm=raw_bpm)


@typ.final
class AnchorEvent(Event):
    """An event representing a tick "locked" to a particular timestamp."""

    _Self = typ.TypeVar("_Self", bound="AnchorEvent")

    @classmethod
    def from_parsed_data(cls: type[_Self], data: AnchorEvent.ParsedData) -> _Self:
        """Obtain an instance of this object from parsed data.

        Args:
            data: The data necessary to create an event. Most likely from a Moonscraper ``.chart``.

        Returns:
            An an instance of this object initialized from ``data``.
        """

        timestamp = datetime.timedelta(microseconds=data.microseconds)
        return cls(tick=data.tick, timestamp=timestamp)

    @typ.final
    @dataclasses.dataclass(kw_only=True, frozen=True, repr=False)
    class ParsedData(Event.ParsedData, DictReprMixin):
        """The data on a single chart line associated with an ``AnchorEvent``.

        This is a ``frozen``, ``kw_only`` dataclass.
        """

        _Self = typ.TypeVar("_Self", bound="AnchorEvent.ParsedData")

        microseconds: int

        # Match 1: Tick
        # Match 2: Microseconds
        _regex: typ.Final[str] = r"^\s*?(\d+?) = A (\d+?)$"
        _regex_prog: typ.Final[typ.Pattern[str]] = re.compile(_regex)

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
            raw_tick, raw_microseconds = m.groups()
            return cls(tick=int(raw_tick), microseconds=int(raw_microseconds))
