"""For representing the data related to tempo and meter.

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
from collections.abc import Sequence
from datetime import timedelta

import chartparse.tick
import chartparse.time
import chartparse.track
from chartparse.event import Event
from chartparse.exceptions import RegexNotMatchError
from chartparse.tick import Tick, Ticks
from chartparse.time import Timestamp
from chartparse.util import DictPropertiesEqMixin, DictReprMixin, DictReprTruncatedSequencesMixin

if typ.TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Iterable

logger = logging.getLogger(__name__)


@typ.final
@dataclasses.dataclass(frozen=True, kw_only=True)
class SyncTrack(DictPropertiesEqMixin, DictReprTruncatedSequencesMixin):
    """All of a :class:`~chartparse.chart.Chart` object's tempo-mapping related events.

    This is a ``frozen``, ``kw_only`` dataclass.
    """

    _Self = typ.TypeVar("_Self", bound="SyncTrack")

    section_name: typ.ClassVar[str] = "SyncTrack"
    """The name of this track's section in a ``.chart`` file."""

    time_signature_events: Sequence[TimeSignatureEvent]
    """A ``SyncTrack``'s ``TimeSignatureEvent``\\ s."""

    bpm_events: BPMEvents
    """A ``SyncTrack``'s ``BPMEvent``\\ s."""

    anchor_events: Sequence[AnchorEvent]
    """A ``SyncTrack``'s ``AnchorEvent``\\ s."""

    def __post_init__(self) -> None:
        """Validates all instance attributes.

        Raises:
            ValueError: If ``time_signature_events`` or ``bpm_events`` is empty, or if either of
                their first elements has a ``tick`` value of ``0``, or if ``resolution`` is not
                positive.
        """
        if not self.time_signature_events:
            raise ValueError("time_signature_events must not be empty")
        if self.time_signature_events[0].tick != 0:
            raise ValueError(
                f"first TimeSignatureEvent {self.time_signature_events[0]} must have tick 0"
            )

    @classmethod
    def from_chart_lines(
        cls: type[_Self],
        resolution: Ticks,
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

        bpm_events = chartparse.track.build_events_from_data(BPMEvent, bpm_data, resolution)

        time_signature_events = chartparse.track.build_events_from_data(
            TimeSignatureEvent, time_signature_data, bpm_events
        )

        anchor_events = chartparse.track.build_events_from_data(AnchorEvent, anchor_data)

        return cls(
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
        bpm_events: BPMEvents,
    ) -> _Self:
        """Obtain an instance of this object from parsed data.

        Args:
            data: The data necessary to create an event. Most likely from a Moonscraper ``.chart``.

            prev_event: The ``TimeSignatureEvent`` with the greatest ``tick`` value less than that
                of this event. If this is ``None``, then this must be the first
                ``TimeSignatureEvent``.

            bpm_events: An object that can be used to get a timestamp at a particular tick.

        Returns:
            An an instance of this object initialized from ``data``.
        """

        # The lower number is written by Moonscraper as the log2 of the true value.
        lower_numeral = 2**data.lower if data.lower is not None else cls._default_lower_numeral
        timestamp, proximal_bpm_event_index = bpm_events.timestamp_at_tick(
            data.tick,
            start_iteration_index=prev_event._proximal_bpm_event_index if prev_event else 0,
        )
        return cls(
            tick=data.tick,
            timestamp=timestamp,
            upper_numeral=data.upper,
            lower_numeral=lower_numeral,
            _proximal_bpm_event_index=proximal_bpm_event_index,
        )

    def __str__(self) -> str:
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
            return cls(tick=Tick(int(raw_tick)), upper=int(raw_upper), lower=lower)


@typ.final
@dataclasses.dataclass(kw_only=True, frozen=True)
class BPMEvent(Event):
    """An event representing a BPM (beats per minute) change at a particular tick.

    This is a ``frozen``, ``kw_only`` dataclass.
    """

    _Self = typ.TypeVar("_Self", bound="BPMEvent")

    bpm: float
    """The beats per minute value. Must not have more than 3 decimal places."""

    def __post_init__(self) -> None:
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
        resolution: Ticks,
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

        if prev_event is None:
            timestamp, proximal_bpm_event_index = Timestamp(timedelta(0)), 0
        else:
            if data.tick <= prev_event.tick:
                # TODO: This branch can be removed if we move chart validation to an external flow.
                raise ValueError(
                    f"{cls.__name__} at tick {data.tick} does not occur after previous "
                    f"{cls.__name__} at tick {prev_event.tick}; tick values of "
                    f"{cls.__name__} must be strictly increasing."
                )
            ticks_since_prev = chartparse.tick.between(prev_event.tick, data.tick)
            seconds_since_prev = chartparse.tick.seconds_from_ticks_at_bpm(
                ticks_since_prev, prev_event.bpm, resolution
            )
            timestamp = chartparse.time.add(
                prev_event.timestamp, timedelta(seconds=seconds_since_prev)
            )
            proximal_bpm_event_index = prev_event._proximal_bpm_event_index + 1

        return cls(
            tick=data.tick,
            timestamp=timestamp,
            bpm=bpm,
            _proximal_bpm_event_index=proximal_bpm_event_index,
        )

    def __str__(self) -> str:
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
            return cls(tick=Tick(int(raw_tick)), raw_bpm=raw_bpm)


@typ.final
@dataclasses.dataclass(kw_only=True, frozen=True)
class BPMEvents(Sequence[BPMEvent]):
    """The chart's ``BPMEvent``\\s, wrapped with the chart's resolution.

    This exists solely to allow ``timestamp_at_tick`` to be called the moment all requisite data is
    accessible.

    This is a ``frozen``, ``kw_only`` dataclass.
    """

    events: Sequence[BPMEvent]
    """The chart's ``BPMEvent``\\s."""

    resolution: Ticks
    """The number of ticks in a quarter note."""

    def __post_init__(self) -> None:
        """Validates all instance attributes.

        Raises:
            ValueError: If ``bpm_events`` is empty, or if its first element has a ``tick`` value of
                ``0``, or if ``resolution`` is not positive.
        """
        if self.resolution <= 0:
            raise ValueError(f"resolution ({self.resolution}) must be positive")
        if not self.events:
            raise ValueError("events must not be empty")
        if self.events[0].tick != 0:
            raise ValueError(f"first BPMEvent {self.events[0]} must have tick 0")

    def __len__(self) -> int:
        return len(self.events)

    @typ.overload
    def __getitem__(self, index: int) -> BPMEvent:
        ...  # pragma: no cover

    @typ.overload
    def __getitem__(self, index: slice) -> Sequence[BPMEvent]:
        ...  # pragma: no cover

    def __getitem__(self, index: int | slice) -> BPMEvent | Sequence[BPMEvent]:
        return self.events[index]

    def timestamp_at_tick_no_optimize_return(
        self, tick: Tick, *, start_iteration_index: int = 0
    ) -> Timestamp:
        """Returns the timestamp at the input tick.

        Args:
            tick: The tick at which the timestamp should be calculated.

        Kwargs:
            start_iteration_index: An optional optimizing input that allows this
                function to start iterating over ``BPMEvent``s at a later index. Only pass this if
                you are certain that the event that should be proximal to ``tick`` is _not_ before
                this index. Not passing this kwarg results only in slower execution.

        Returns:
            The timestamp at the input tick.
        """
        timestamp, _ = self.timestamp_at_tick(tick, start_iteration_index=start_iteration_index)
        return timestamp

    def timestamp_at_tick(
        self, tick: Tick, *, start_iteration_index: int = 0
    ) -> tuple[Timestamp, int]:
        """Returns the timestamp at the input tick, and an optimizing value.

        Args:
            tick: The tick at which the timestamp should be calculated.

        Kwargs:
            start_iteration_index: An optional optimizing input that allows this
                function to start iterating over ``BPMEvent``s at a later index. Only pass this if
                you are certain that the event that should be proximal to ``tick`` is _not_ before
                this index. Not passing this kwarg results only in slower execution.

        Returns:
            The timestamp at the input tick, plus the index of the ``BPMEvent`` proximal to the
            input tick. This index can be passed to successive calls to this function via
            ``start_iteration_index`` as an optimization.
        """
        proximal_bpm_event_index = self._index_of_proximal_event(
            tick, start_iteration_index=start_iteration_index
        )
        proximal_bpm_event = self.events[proximal_bpm_event_index]
        ticks_since_proximal_bpm_event = chartparse.tick.between(proximal_bpm_event.tick, tick)
        seconds_since_proximal_bpm_event = chartparse.tick.seconds_from_ticks_at_bpm(
            ticks_since_proximal_bpm_event,
            proximal_bpm_event.bpm,
            self.resolution,
        )
        timestamp = chartparse.time.add(
            proximal_bpm_event.timestamp, seconds_since_proximal_bpm_event
        )
        return timestamp, proximal_bpm_event_index

    def _index_of_proximal_event(self, tick: Tick, start_iteration_index: int = 0) -> int:
        index_of_last_event = len(self) - 1
        if start_iteration_index > index_of_last_event:
            raise ValueError(
                f"there are no BPMEvents at or after index {start_iteration_index} in bpm_events"
            )

        first_event = self[start_iteration_index]
        if first_event.tick > tick:
            raise ValueError(
                f"input tick {tick} precedes tick value of first BPMEvent ({first_event.tick})"
            )

        # Do NOT iterate over last BPMEvent, since it has no next event.
        for index in range(start_iteration_index, index_of_last_event):
            if self[index + 1].tick > tick:
                return index

        # If none of the previous BPMEvents are proximal, the last event is proximal by
        # definition.
        return index_of_last_event


@typ.final
@dataclasses.dataclass(kw_only=True, frozen=True)
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

        timestamp = Timestamp(timedelta(microseconds=data.microseconds))
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
            return cls(tick=Tick(int(raw_tick)), microseconds=int(raw_microseconds))
