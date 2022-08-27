"""For representing the data related to tempo and meter.

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
from typing import Final, Optional, Pattern, Type, TypeVar

import chartparse.tick
import chartparse.track
from chartparse.datastructures import ImmutableSortedList
from chartparse.event import Event, TimestampAtTickSupporter
from chartparse.exceptions import RegexNotMatchError
from chartparse.util import DictPropertiesEqMixin, DictReprTruncatedSequencesMixin

SyncTrackT = TypeVar("SyncTrackT", bound="SyncTrack")

logger = logging.getLogger(__name__)


@typing.final
class SyncTrack(DictPropertiesEqMixin, DictReprTruncatedSequencesMixin):
    """All of a :class:`~chartparse.chart.Chart` object's tempo-mapping related events."""

    resolution: Final[int]
    """The number of ticks for which a quarter note lasts."""

    time_signature_events: Final[Sequence[TimeSignatureEvent]]
    """A ``SyncTrack``'s ``TimeSignatureEvent``\\ s."""

    bpm_events: Final[ImmutableSortedList[BPMEvent]]
    """A ``SyncTrack``'s ``BPMEvent``\\ s."""

    section_name: Final[str] = "SyncTrack"
    """The name of this track's section in a ``.chart`` file."""

    def __init__(
        self,
        resolution: int,
        time_signature_events: Sequence[TimeSignatureEvent],
        bpm_events: ImmutableSortedList[BPMEvent],
    ):
        """Instantiates and validates all instance attributes.

        Raises:
            ValueError: If ``time_signature_events`` or ``bpm_events`` is empty, or if either of
                their first elements has a ``tick`` value of ``0``.
        """
        if resolution <= 0:
            raise ValueError(f"resolution ({resolution}) must be positive")
        if not time_signature_events:
            raise ValueError("time_signature_events must not be empty")
        if time_signature_events[0].tick != 0:
            raise ValueError(
                f"first TimeSignatureEvent {time_signature_events[0]} must have tick 0"
            )
        if not bpm_events:
            raise ValueError("bpm_events must not be empty")
        if bpm_events[0].tick != 0:
            raise ValueError(f"first BPMEvent {bpm_events[0]} must have tick 0")

        self.resolution = resolution
        self.time_signature_events = time_signature_events
        self.bpm_events = bpm_events

    @classmethod
    def from_chart_lines(
        cls: Type[SyncTrackT],
        resolution: int,
        iterator_getter: Callable[[], Iterable[str]],
    ) -> SyncTrackT:
        """Initializes instance attributes by parsing an iterable of strings.

        Args:
            resolution: The number of ticks in a quarter note.
            iterator_getter: The iterable of strings returned by this is most likely from a
                Moonscraper ``.chart``. Must be a function so the strings can be iterated over
                multiple times, if necessary.

        Returns:
            A ``SyncTrack`` parsed from the strings returned by ``iterator_getter``.
        """

        bpm_events: ImmutableSortedList[BPMEvent] = chartparse.track.parse_events_from_chart_lines(
            iterator_getter(), BPMEvent.from_chart_line, resolution
        )

        class TimestampAtTicker(object):
            resolution: Final[int]

            def __init__(self, resolution: int):
                self.resolution = resolution

            def timestamp_at_tick(
                self, tick: int, start_bpm_event_index: int = 0
            ) -> tuple[datetime.timedelta, int]:
                return cls._timestamp_at_tick(
                    bpm_events, tick, self.resolution, start_bpm_event_index
                )  # pragma: no cover

        tatter = TimestampAtTicker(resolution)

        time_signature_events: ImmutableSortedList[
            TimeSignatureEvent
        ] = chartparse.track.parse_events_from_chart_lines(
            iterator_getter(),
            TimeSignatureEvent.from_chart_line,
            tatter,
        )
        return cls(resolution, time_signature_events, bpm_events)

    def timestamp_at_tick(
        self, tick: int, start_bpm_event_index: int = 0
    ) -> tuple[datetime.timedelta, int]:
        """Returns the timestamp at the input tick.

        Args:
            tick: The tick at which the timestamp should be calculated.

        Kwargs:
            start_bpm_event_index: An optional optimizing input that allows this function to start
                iterating over ``BPMEvent``s at a later index. Only pass this if you are certain
                that the event that should be proximal to ``tick`` is _not_ before this index.

        Returns:
            The timestamp at the input tick, plus the index of the ``BPMEvent`` proximal to the
            input tick. This index can be passed to successive calls to this function via
            ``start_bpm_event_index`` as an optimization.
        """
        return self._timestamp_at_tick(
            self.bpm_events, tick, self.resolution, start_bpm_event_index=start_bpm_event_index
        )

    @staticmethod
    def _timestamp_at_tick(
        bpm_events: ImmutableSortedList[BPMEvent],
        tick: int,
        resolution: int,
        start_bpm_event_index: int = 0,
    ) -> tuple[datetime.timedelta, int]:
        """Allows ``timestamp_at_tick`` to be used by injecting a ``bpm_events`` object."""

        proximal_bpm_event_idx = SyncTrack._idx_of_proximal_bpm_event(
            bpm_events, tick, start_idx=start_bpm_event_index
        )
        proximal_bpm_event = bpm_events[proximal_bpm_event_idx]
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
        return timestamp, proximal_bpm_event_idx

    @staticmethod
    def _idx_of_proximal_bpm_event(
        bpm_events: ImmutableSortedList[BPMEvent], tick: int, start_idx: int = 0
    ) -> int:
        if not bpm_events:
            raise ValueError("bpm_events must not be empty")

        idx_of_last_event = bpm_events.length - 1
        if start_idx > idx_of_last_event:
            raise ValueError(f"there are no BPMEvents at or after index {start_idx} in bpm_events")

        first_event = bpm_events[start_idx]
        if first_event.tick > tick:
            raise ValueError(
                f"input tick {tick} precedes tick value of first BPMEvent ({first_event.tick})"
            )

        use_binary_search = False
        if use_binary_search:  # pragma: no cover
            return bpm_events.find_le(
                tick, lo=start_idx, hi=bpm_events.length, key=lambda e: e.tick
            )
        else:
            # Do NOT iterate over last BPMEvent, since it has no next event.
            for idx in range(start_idx, idx_of_last_event):
                if bpm_events[idx + 1].tick > tick:
                    return idx

            # If none of the previous BPMEvents are proximal, the last event is proximal by
            # definition.
            return idx_of_last_event


TimeSignatureEventT = TypeVar("TimeSignatureEventT", bound="TimeSignatureEvent")


@typing.final
class TimeSignatureEvent(Event):
    """An event representing a time signature change at a particular tick."""

    upper_numeral: Final[int]
    """The number indicating how many beats constitute a bar."""

    lower_numeral: Final[int]
    """The number indicating the note value that represents one beat."""

    # Match 1: Tick
    # Match 2: Upper numeral
    # Match 3: Lower numeral (optional; assumed to be 4 if absent)
    _regex: Final[str] = r"^\s*?(\d+?) = TS (\d+?)(?: (\d+?))?\s*?$"
    _regex_prog: Final[Pattern[str]] = re.compile(_regex)

    _default_lower_numeral: Final[int] = 4

    def __init__(
        self,
        tick: int,
        timestamp: datetime.timedelta,
        upper_numeral: int,
        lower_numeral: int,
        proximal_bpm_event_idx: int = 0,
    ):
        """Initializes all instance attributes."""

        super().__init__(tick, timestamp, proximal_bpm_event_idx=proximal_bpm_event_idx)
        self.upper_numeral = upper_numeral
        self.lower_numeral = lower_numeral

    @classmethod
    def from_chart_line(
        cls: Type[TimeSignatureEventT],
        line: str,
        prev_event: Optional[TimeSignatureEventT],
        tatter: TimestampAtTickSupporter,
    ) -> TimeSignatureEventT:
        """Attempt to obtain an instance of this object from a string.

        Args:
            line: Most likely a line from a Moonscraper ``.chart``.
            prev_event: The ``TimeSignatureEvent`` with the greatest ``tick`` value less than that
                of this event. If this is ``None``, then this must be the first
                ``TimeSignatureEvent``.
            tatter: An object that can be used to get a timestamp at a particular tick.

        Returns:
            An an instance of this object parsed from ``line``.

        Raises:
            RegexNotMatchError: If the mixed-into class' ``_regex`` does not match ``line``.
        """

        m = cls._regex_prog.match(line)
        if not m:
            raise RegexNotMatchError(cls._regex, line)
        tick, upper_numeral = int(m.group(1)), int(m.group(2))
        # The lower number is written by Moonscraper as the log2 of the true value.
        lower_numeral = 2 ** int(m.group(3)) if m.group(3) else cls._default_lower_numeral
        timestamp, proximal_bpm_event_idx = cls.calculate_timestamp(tick, prev_event, tatter)
        return cls(
            tick,
            timestamp,
            upper_numeral,
            lower_numeral,
            proximal_bpm_event_idx=proximal_bpm_event_idx,
        )

    def __str__(self) -> str:  # pragma: no cover
        to_join = [super().__str__()]
        to_join.append(f": {self.upper_numeral}/{self.lower_numeral}")
        return "".join(to_join)


BPMEventT = TypeVar("BPMEventT", bound="BPMEvent")


@typing.final
class BPMEvent(Event):
    """An event representing a BPM (beats per minute) change at a particular tick."""

    bpm: Final[float]
    """The beats per minute value. Must not have more than 3 decimal places."""

    # Match 1: Tick
    # Match 2: BPM (the last 3 digits are the decimal places)
    _regex: Final[str] = r"^\s*?(\d+?) = B (\d+?)\s*?$"
    _regex_prog: Final[Pattern[str]] = re.compile(_regex)

    def __init__(
        self, tick: int, timestamp: datetime.timedelta, bpm: float, proximal_bpm_event_idx: int = 0
    ):
        """Initialize all instance attributes.

        Raises:
            ValueError: If ``bpm`` has more than 3 decimal places.
        """
        if round(bpm, 3) != bpm:
            raise ValueError(f"bpm {bpm} must not have more than 3 decimal places.")
        super().__init__(tick, timestamp, proximal_bpm_event_idx=proximal_bpm_event_idx)
        self.bpm = bpm

    # TODO: Refactor all regex matching for all `from_chart_line` functions to a match method for
    # better unit testability.
    @classmethod
    def from_chart_line(
        cls: Type[BPMEventT], line: str, prev_event: Optional[BPMEventT], resolution: int
    ) -> BPMEventT:
        """Attempt to obtain an instance of this object from a string.

        Args:
            line: Most likely a line from a Moonscraper ``.chart``.
            prev_event: The ``BPMEvent`` with the greatest ``tick`` value less than that of this
                event. If this is ``None``, then this must be the first ``BPMEvent``.
            resolution: The number of ticks in a quarter note.

        Returns:
            An an instance of this object parsed from ``line``.

        Raises:
            RegexNotMatchError: If the mixed-into class' ``_regex`` does not match ``line``.
            ValueError: If ``prev_event.tick`` is not less than the tick value parsed from
                ``line``.
        """

        m = cls._regex_prog.match(line)
        if not m:
            raise RegexNotMatchError(cls._regex, line)

        tick, raw_bpm = int(m.group(1)), m.group(2)

        bpm_whole_part_str, bpm_decimal_part_str = raw_bpm[:-3], raw_bpm[-3:]
        bpm_whole_part = int(bpm_whole_part_str) if bpm_whole_part_str != "" else 0
        bpm_decimal_part = int(bpm_decimal_part_str) / 1000
        bpm = bpm_whole_part + bpm_decimal_part

        class TimestampAtTicker(object):
            resolution: Final[int]

            def __init__(self, resolution: int):
                self.resolution = resolution

            def timestamp_at_tick(
                self, tick: int, start_bpm_event_index: int = 0
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
                return timestamp, start_bpm_event_index

        tatter = TimestampAtTicker(resolution)
        timestamp, proximal_bpm_event_idx = cls.calculate_timestamp(tick, prev_event, tatter)
        return cls(tick, timestamp, bpm, proximal_bpm_event_idx=proximal_bpm_event_idx)

    def __str__(self) -> str:  # pragma: no cover
        to_join = [super().__str__()]
        to_join.append(f": {self.bpm} BPM")
        return "".join(to_join)
