"""For representing the data related to a single (instrument, difficulty) pair.

You should not need to create any of this module's objects manually; please instead create a
:class:`~chartparse.chart.Chart` and inspect its attributes via that object.

.. _Google Python Style Guide:
    http://google.github.io/styleguide/pyguide.html

"""

from __future__ import annotations

import collections
import dataclasses
import datetime
import enum
import functools
import logging
import re
import typing
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from enum import Enum
from typing import ClassVar, Final, Optional, Pattern, Type, TypeVar, Union

import chartparse.tick
import chartparse.track
from chartparse.datastructures import ImmutableList, ImmutableSortedList
from chartparse.event import Event, TimestampAtTickSupporter
from chartparse.exceptions import ProgrammerError, RegexNotMatchError
from chartparse.tick import NoteDuration
from chartparse.util import (
    AllValuesGettableEnum,
    DictPropertiesEqMixin,
    DictReprTruncatedSequencesMixin,
)

logger = logging.getLogger(__name__)

InstrumentTrackT = TypeVar("InstrumentTrackT", bound="InstrumentTrack")


@typing.final
@enum.unique
class Difficulty(AllValuesGettableEnum):
    """An :class:`~chartparse.instrument.InstrumentTrack`'s difficulty setting.

    Note that this is distinct from the numeric representation of the difficulty of playing a
    chart. That number is referred to as "intensity".
    """

    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"
    EXPERT = "Expert"


@typing.final
@enum.unique
class Instrument(AllValuesGettableEnum):
    """The instrument to which a :class:`~chartparse.instrument.InstrumentTrack` corresponds."""

    GUITAR = "Single"
    GUITAR_COOP = "DoubleGuitar"
    BASS = "DoubleBass"
    RHYTHM = "DoubleRhythm"
    KEYS = "Keyboard"
    DRUMS = "Drums"
    GHL_GUITAR = "GHLGuitar"  # Guitar (Guitar Hero: Live)
    GHL_BASS = "GHLBass"  # Bass (Guitar Hero: Live)


@typing.final
class Note(Enum):
    """The note lane(s) to which a :class:`~chartparse.instrument.NoteEvent` corresponds."""

    P = bytearray((0, 0, 0, 0, 0))
    G = bytearray((1, 0, 0, 0, 0))
    GR = bytearray((1, 1, 0, 0, 0))
    GY = bytearray((1, 0, 1, 0, 0))
    GB = bytearray((1, 0, 0, 1, 0))
    GO = bytearray((1, 0, 0, 0, 1))
    GRY = bytearray((1, 1, 1, 0, 0))
    GRB = bytearray((1, 1, 0, 1, 0))
    GRO = bytearray((1, 1, 0, 0, 1))
    GYB = bytearray((1, 0, 1, 1, 0))
    GYO = bytearray((1, 0, 1, 0, 1))
    GBO = bytearray((1, 0, 0, 1, 1))
    GRYB = bytearray((1, 1, 1, 1, 0))
    GRYO = bytearray((1, 1, 1, 0, 1))
    GRBO = bytearray((1, 1, 0, 1, 1))
    GYBO = bytearray((1, 0, 1, 1, 1))
    GRYBO = bytearray((1, 1, 1, 1, 1))
    R = bytearray((0, 1, 0, 0, 0))
    RY = bytearray((0, 1, 1, 0, 0))
    RB = bytearray((0, 1, 0, 1, 0))
    RO = bytearray((0, 1, 0, 0, 1))
    RYB = bytearray((0, 1, 1, 1, 0))
    RYO = bytearray((0, 1, 1, 0, 1))
    RBO = bytearray((0, 1, 0, 1, 1))
    RYBO = bytearray((0, 1, 1, 1, 1))
    Y = bytearray((0, 0, 1, 0, 0))
    YB = bytearray((0, 0, 1, 1, 0))
    YO = bytearray((0, 0, 1, 0, 1))
    YBO = bytearray((0, 0, 1, 1, 1))
    B = bytearray((0, 0, 0, 1, 0))
    BO = bytearray((0, 0, 0, 1, 1))
    O = bytearray((0, 0, 0, 0, 1))  # noqa: E741
    # Aliases
    OPEN = bytearray((0, 0, 0, 0, 0))
    GREEN = bytearray((1, 0, 0, 0, 0))
    GREEN_RED = bytearray((1, 1, 0, 0, 0))
    GREEN_YELLOW = bytearray((1, 0, 1, 0, 0))
    GREEN_BLUE = bytearray((1, 0, 0, 1, 0))
    GREEN_ORANGE = bytearray((1, 0, 0, 0, 1))
    GREEN_RED_YELLOW = bytearray((1, 1, 1, 0, 0))
    GREEN_RED_BLUE = bytearray((1, 1, 0, 1, 0))
    GREEN_RED_ORANGE = bytearray((1, 1, 0, 0, 1))
    GREEN_YELLOW_BLUE = bytearray((1, 0, 1, 1, 0))
    GREEN_YELLOW_ORANGE = bytearray((1, 0, 1, 0, 1))
    GREEN_BLUE_ORANGE = bytearray((1, 0, 0, 1, 1))
    GREEN_RED_YELLOW_BLUE = bytearray((1, 1, 1, 1, 0))
    GREEN_RED_YELLOW_ORANGE = bytearray((1, 1, 1, 0, 1))
    GREEN_RED_BLUE_ORANGE = bytearray((1, 1, 0, 1, 1))
    GREEN_YELLOW_BLUE_ORANGE = bytearray((1, 0, 1, 1, 1))
    GREEN_RED_YELLOW_BLUE_ORANGE = bytearray((1, 1, 1, 1, 1))
    RED = bytearray((0, 1, 0, 0, 0))
    RED_YELLOW = bytearray((0, 1, 1, 0, 0))
    RED_BLUE = bytearray((0, 1, 0, 1, 0))
    RED_ORANGE = bytearray((0, 1, 0, 0, 1))
    RED_YELLOW_BLUE = bytearray((0, 1, 1, 1, 0))
    RED_YELLOW_ORANGE = bytearray((0, 1, 1, 0, 1))
    RED_BLUE_ORANGE = bytearray((0, 1, 0, 1, 1))
    RED_YELLOW_BLUE_ORANGE = bytearray((0, 1, 1, 1, 1))
    YELLOW = bytearray((0, 0, 1, 0, 0))
    YELLOW_BLUE = bytearray((0, 0, 1, 1, 0))
    YELLOW_ORANGE = bytearray((0, 0, 1, 0, 1))
    YELLOW_BLUE_ORANGE = bytearray((0, 0, 1, 1, 1))
    BLUE = bytearray((0, 0, 0, 1, 0))
    BLUE_ORANGE = bytearray((0, 0, 0, 1, 1))
    ORANGE = bytearray((0, 0, 0, 0, 1))

    def is_chord(self):
        """Returns whether this ``Note`` has multiple active lanes."""

        return sum(self.value) > 1


@typing.final
class NoteTrackIndex(AllValuesGettableEnum):
    """The integer in a line in a Moonscraper ``.chart`` file's instrument track."""

    G = 0
    R = 1
    Y = 2
    B = 3
    O = 4  # noqa: E741
    P = 7
    FORCED = 5
    TAP = 6
    # Aliases
    GREEN = 0
    RED = 1
    YELLOW = 2
    BLUE = 3
    ORANGE = 4
    OPEN = 7


# TODO: create newtype (?) for bytearray for note array.


@typing.final
class InstrumentTrack(DictPropertiesEqMixin, DictReprTruncatedSequencesMixin):
    """All of the instrument-related events for one (instrument, difficulty) pair."""

    resolution: Final[int]
    """The number of ticks for which a quarter note lasts."""

    instrument: Final[Instrument]
    """The instrument to which this track corresponds."""

    difficulty: Final[Difficulty]
    """This track's difficulty setting."""

    # TODO: All of these sequences of events should probably be individual objects so things like
    # _last_note_timestamp can live more tightly coupled to the actual events.
    note_events: Final[Sequence[NoteEvent]]
    """An (instrument, difficulty) pair's ``NoteEvent`` objects."""

    star_power_events: Final[ImmutableSortedList[StarPowerEvent]]
    """An (instrument, difficulty) pair's ``StarPowerEvent`` objects."""

    _min_note_instrument_track_index = 0
    _max_note_instrument_track_index = 4
    _open_instrument_track_index = 7
    _forced_instrument_track_index = 5
    _tap_instrument_track_index = 6

    _unhandled_note_track_index_log_msg_tmpl: Final[str] = "unhandled note track index {}"

    def __init__(
        self,
        resolution: int,
        instrument: Instrument,
        difficulty: Difficulty,
        note_events: Sequence[NoteEvent],
        star_power_events: ImmutableSortedList[StarPowerEvent],
    ) -> None:
        """Instantiates all instance attributes."""
        if resolution <= 0:
            raise ValueError(f"resolution ({resolution}) must be positive")

        self.resolution = resolution
        self.instrument = instrument
        self.difficulty = difficulty
        self.note_events = note_events
        self.star_power_events = star_power_events

    @functools.cached_property
    def section_name(self) -> str:
        """The concatenation of this track's difficulty and instrument (in that order)."""
        return self.difficulty.value + self.instrument.value

    @functools.cached_property
    def last_note_end_timestamp(self) -> Optional[datetime.timedelta]:
        """The timestamp at which the :attr:`~chartparse.instrument.NoteEvent.sustain` value of the
        last :class:`~chartparse.instrument.NoteEvent` ends.

        This is ``None`` iff the track has no notes.
        """
        if not self.note_events:
            return None
        return max(self.note_events, key=lambda e: e.end_timestamp).end_timestamp

    @classmethod
    def from_chart_lines(
        cls: Type[InstrumentTrackT],
        instrument: Instrument,
        difficulty: Difficulty,
        iterator_getter: Callable[[], Iterable[str]],
        tatter: TimestampAtTickSupporter,
    ) -> InstrumentTrackT:
        """Initializes instance attributes by parsing an iterable of strings.

        Args:
            instrument: The instrument to which this track corresponds.
            difficulty: This track's difficulty setting.
            iterator_getter: The iterable of strings returned by this strings is most likely from a
                Moonscraper ``.chart``. Must be a function so the strings can be iterated over
                multiple times, if necessary.
            tatter: An object that can be used to get a timestamp at a particular tick.

        Returns:
            An ``InstrumentTrack`` parsed from the strings returned by ``iterator_getter``.
        """

        star_power_data = cls._parse_data_from_chart_lines(iterator_getter())
        star_power_events = chartparse.track.build_events_from_data(
            star_power_data,
            StarPowerEvent.from_parsed_data,
            tatter,
        )
        note_events = cls._parse_note_events_from_chart_lines(
            iterator_getter(), star_power_events, tatter
        )
        return cls(tatter.resolution, instrument, difficulty, note_events, star_power_events)

    @classmethod
    def _parse_data_from_chart_lines(
        cls: Type[InstrumentTrackT],
        lines: Iterable[str],
    ) -> ImmutableList[StarPowerEvent.ParsedData]:
        parsed_data = chartparse.track.parse_data_from_chart_lines((StarPowerEvent,), lines)
        star_power_data = typing.cast(
            ImmutableList[StarPowerEvent.ParsedData],
            parsed_data[StarPowerEvent],
        )
        return star_power_data

    def __str__(self) -> str:  # pragma: no cover
        return (
            f"{type(self).__name__}"
            f"(instrument: {self.instrument}, "
            f"difficulty: {self.difficulty}, "
            f"len(note_events): {len(self.note_events)}, "
            f"len(star_power_events): {len(self.star_power_events)})"
        )

    @classmethod
    def _parse_note_events_from_chart_lines(
        cls,
        chart_lines: Iterable[str],
        star_power_events: ImmutableSortedList[StarPowerEvent],
        tatter: TimestampAtTickSupporter,
    ) -> ImmutableSortedList[NoteEvent]:
        note_arrays, sustain_lists, is_taps, is_forceds = cls._parse_tick_dicts_from_chart_lines(
            chart_lines
        )

        proximal_bpm_event_index = 0
        star_power_event_index = 0
        events: list[NoteEvent] = []
        for note_tick in sorted(note_arrays.keys()):
            previous_event = events[-1] if events else None
            event, proximal_bpm_event_index, star_power_event_index = NoteEvent.from_parsed_data(
                note_tick,
                note_arrays[note_tick],
                tuple(sustain_lists[note_tick]),
                is_taps[note_tick],
                is_forceds[note_tick],
                previous_event,
                star_power_events,
                tatter,
                proximal_bpm_event_index=proximal_bpm_event_index,
                star_power_event_index=star_power_event_index,
            )
            events.append(event)

        # This is already sorted because we iterate over `sorted(note_arrays.keys())`.
        return ImmutableSortedList(events, already_sorted=True)

    @classmethod
    def _parse_tick_dicts_from_chart_lines(
        cls,
        chart_lines: Iterable[str],
    ) -> tuple[
        collections.defaultdict[int, bytearray],
        collections.defaultdict[int, list[Optional[int]]],
        collections.defaultdict[int, bool],
        collections.defaultdict[int, bool],
    ]:
        note_arrays: collections.defaultdict[int, bytearray] = collections.defaultdict(
            lambda: bytearray(5)
        )
        sustain_lists: collections.defaultdict[int, list[Optional[int]]] = collections.defaultdict(
            lambda: [None] * 5
        )
        is_taps = collections.defaultdict(bool)
        is_forceds = collections.defaultdict(bool)

        for line in chart_lines:
            m = NoteEvent._regex_prog.match(line)
            if not m:
                continue
            tick, note_index, sustain = int(m.group(1)), int(m.group(2)), int(m.group(3))
            if (
                InstrumentTrack._min_note_instrument_track_index
                <= note_index
                <= InstrumentTrack._max_note_instrument_track_index
            ):
                note_arrays[tick][note_index] = 1
                sustain_lists[tick][note_index] = sustain
            elif note_index == InstrumentTrack._open_instrument_track_index:
                # Because `note_arrays` is a defaultdict, simply accessing it at `tick` is
                # sufficient to conjure a bytearray representing an open note.
                note_arrays[tick]
                sustain_lists[tick]
            elif note_index == InstrumentTrack._tap_instrument_track_index:
                is_taps[tick] = True
            elif note_index == InstrumentTrack._forced_instrument_track_index:
                is_forceds[tick] = True
            else:  # pragma: no cover
                # TODO: Once _parse_note_events_from_chart_lines has its own unit tests, cover this
                # branch.
                logger.warning(cls._unhandled_note_track_index_log_msg_tmpl.format(note_index))

        return note_arrays, sustain_lists, is_taps, is_forceds


@typing.final
@dataclasses.dataclass
class NoteEventParsedData(object):
    tick: int
    note_index: int
    sustain: int


@typing.final
@dataclass
class StarPowerData(DictPropertiesEqMixin):
    """Star power related info for a :class:`~chartparse.instrument.NoteEvent`."""

    # This is conceptually Final, but annotating it as such confuses mypy into thinking it should
    # be ClassVar.
    star_power_event_index: int


SustainTupleT = tuple[Optional[int], ...]
"""A 5-element tuple representing the sustain value of each note lane for nonuniform sustains.

An element is ``None`` if and only if the corresponding note lane is inactive. If an element is
``0``, then there must be at least one other non-``0``, non-``None`` element; this is because that
``0`` element represents an unsustained note in unison with a sustained note.
"""

ComplexNoteSustainT = Union[int, SustainTupleT]
"""A sustain value that can capture multiple coinciding notes with different sustain values.

If this value is an ``int``, it means that all active note lanes at this tick value are sustained
for the same number of ticks. If this value is ``0``, then none of the note lanes are active.
"""


@typing.final
@enum.unique
class HOPOState(Enum):
    """The manner in which a :class:`~chartparse.instrument.NoteEvent` can/must be hit."""

    STRUM = 0
    HOPO = 1
    TAP = 2


NoteEventT = TypeVar("NoteEventT", bound="NoteEvent")


@typing.final
class NoteEvent(Event):
    """An event representing all of the notes at a particular tick.

    A note event's ``str`` representation looks like this::

        NoteEvent(t@0000816 0:00:02.093750): sustain=0: Note.Y [flags=H]

    This event occurs at tick 816 and timestamp 0:00:02.093750. It is not sustained. It is yellow.
    It is a HOPO. Other valid flags are ``T`` (for "tap") and ``S`` (for "strum").

    """

    note: Final[Note]
    """The note lane(s) that are active."""

    sustain: Final[ComplexNoteSustainT]
    """Information about this note event's sustain value."""

    end_timestamp: Final[datetime.timedelta]
    """The timestamp at which this note ends."""

    hopo_state: Final[HOPOState]
    """Whether the note is a strum, a HOPO, or a tap note."""

    star_power_data: Final[Optional[StarPowerData]]
    """Information associated with star power for this note.

    If this is ``None``, then the note is not a star power note.
    """

    # This regex matches a single "N" line within a instrument track section,
    # but this class should be used to represent all of the notes at a
    # particular tick. This means that you might need to consolidate multiple
    # "N" lines into a single NoteEvent, e.g. for chords.
    # Match 1: Tick
    # Match 2: Note index
    # Match 3: Sustain (ticks)
    _regex: Final[str] = r"^\s*?(\d+?) = N (\d+?) (\d+?)\s*?$"
    _regex_prog: Final[Pattern[str]] = re.compile(_regex)

    def __init__(
        self,
        tick: int,
        timestamp: datetime.timedelta,
        end_timestamp: datetime.timedelta,
        note: Note,
        hopo_state: HOPOState,
        sustain: ComplexNoteSustainT = 0,
        star_power_data: Optional[StarPowerData] = None,
        proximal_bpm_event_index: int = 0,
    ) -> None:
        super().__init__(tick, timestamp, proximal_bpm_event_index=proximal_bpm_event_index)
        self.end_timestamp = end_timestamp
        self.note = note
        self.hopo_state = hopo_state
        self.sustain = self._refine_sustain(sustain)
        self.star_power_data = star_power_data

    @functools.cached_property
    def longest_sustain(self) -> int:
        if isinstance(self.sustain, int):
            return self.sustain
        elif isinstance(self.sustain, tuple):
            if all(s is None for s in self.sustain):
                raise ValueError("all sustain values are `None`")
            return max(s for s in self.sustain if s is not None)
        else:
            raise ProgrammerError  # pragma: no cover

    @functools.cached_property
    def end_tick(self) -> int:
        return self.tick + self.longest_sustain

    @classmethod
    def from_parsed_data(
        cls: Type[NoteEventT],
        tick: int,
        note_array: bytearray,
        sustain: SustainTupleT,
        is_tap: bool,
        is_forced: bool,
        previous_event: Optional[NoteEvent],
        star_power_events: ImmutableSortedList[StarPowerEvent],
        tatter: TimestampAtTickSupporter,
        proximal_bpm_event_index: int = 0,
        star_power_event_index: int = 0,
    ) -> tuple[NoteEventT, int, int]:
        note = Note(note_array)

        timestamp, proximal_bpm_event_index = tatter.timestamp_at_tick(
            tick, proximal_bpm_event_index=proximal_bpm_event_index
        )

        hopo_state = NoteEvent._compute_hopo_state(
            tatter.resolution,
            tick,
            note,
            is_tap,
            is_forced,
            previous_event,
        )

        star_power_data, star_power_event_index = NoteEvent._compute_star_power_data(
            tick, star_power_events, proximal_star_power_event_index=star_power_event_index
        )

        end_timestamp, _ = tatter.timestamp_at_tick(
            tick, proximal_bpm_event_index=proximal_bpm_event_index
        )

        event = cls(
            tick,
            timestamp,
            end_timestamp,
            note,
            hopo_state,
            sustain=sustain,
            proximal_bpm_event_index=proximal_bpm_event_index,
            star_power_data=star_power_data,
        )
        return event, proximal_bpm_event_index, star_power_event_index

    @staticmethod
    @functools.lru_cache
    def _refine_sustain(sustain: ComplexNoteSustainT) -> ComplexNoteSustainT:
        if isinstance(sustain, tuple):
            if all(d is None or d == 0 for d in sustain):
                return 0
            first_non_none_sustain = next(d for d in sustain if d is not None)
            if all(d is None or d == first_non_none_sustain for d in sustain):
                return first_non_none_sustain
        return sustain

    @staticmethod
    def _compute_hopo_state(
        resolution: int,
        tick: int,
        note: Note,
        is_tap: bool,
        is_forced: bool,
        previous: Optional[NoteEvent],
    ) -> HOPOState:
        if is_forced and previous is None:
            raise ValueError("cannot force the first note in a chart")

        if is_tap:
            return HOPOState.TAP

        # The Moonscraper UI does not allow the first note to be forced, so it must be a strum if
        # it is not a tap.
        if previous is None:
            return HOPOState.STRUM

        eighth_triplet_tick_boundary = chartparse.tick.calculate_ticks_between_notes(
            resolution, NoteDuration.EIGHTH_TRIPLET
        )
        ticks_since_previous = tick - previous.tick
        previous_is_within_eighth_triplet = ticks_since_previous <= eighth_triplet_tick_boundary
        previous_note_is_different = note != previous.note
        should_be_hopo = (
            previous_is_within_eighth_triplet
            and previous_note_is_different
            and not note.is_chord()
        )

        if should_be_hopo != is_forced:
            return HOPOState.HOPO
        else:
            return HOPOState.STRUM

    @staticmethod
    def _compute_star_power_data(
        tick: int,
        star_power_events: ImmutableSortedList[StarPowerEvent],
        *,
        proximal_star_power_event_index: int = 0,
    ) -> tuple[Optional[StarPowerData], int]:
        if not star_power_events:
            return None, 0

        if proximal_star_power_event_index >= star_power_events.length:
            raise ValueError(
                "there are no StarPowerEvents at or after index "
                f"{proximal_star_power_event_index} in star_power_events"
            )

        for candidate_index in range(proximal_star_power_event_index, star_power_events.length):
            if not star_power_events[candidate_index].tick_is_after_event(tick):
                break

        candidate = star_power_events[candidate_index]
        if not candidate.tick_is_in_event(tick):
            return None, candidate_index

        return StarPowerData(candidate_index), candidate_index

    def __str__(self) -> str:  # pragma: no cover
        to_join = [super().__str__()]
        to_join.append(f": sustain={self.sustain}")
        to_join.append(f": {self.note}")

        if self.star_power_data:
            to_join.append("*")

        flags = []
        if self.hopo_state == HOPOState.TAP:
            flags.append("T")
        elif self.hopo_state == HOPOState.HOPO:
            flags.append("H")
        elif self.hopo_state == HOPOState.STRUM:
            flags.append("S")
        if flags:
            to_join.extend([" [hopo_state=", "".join(flags), "]"])

        return "".join(to_join)


SpecialEventT = TypeVar("SpecialEventT", bound="SpecialEvent")


class SpecialEvent(Event):
    """Provides a regex template for parsing 'S' style chart lines.

    This is typically used only as a base class for more specialized subclasses.
    """

    sustain: Final[int]
    """The number of ticks for which this event is sustained.

    This event does _not_ overlap events at ``tick + sustain``; it ends immediately before that
    tick.
    """

    def __init__(
        self,
        tick: int,
        timestamp: datetime.timedelta,
        sustain: int,
        proximal_bpm_event_index: int = 0,
    ) -> None:
        super().__init__(tick, timestamp, proximal_bpm_event_index=proximal_bpm_event_index)
        self.sustain = sustain

    @functools.cached_property
    def end_tick(self) -> int:
        return self.tick + self.sustain

    @classmethod
    def from_parsed_data(
        cls: Type[SpecialEventT],
        data: SpecialEvent.ParsedData,
        prev_event: Optional[SpecialEventT],
        tatter: TimestampAtTickSupporter,
    ) -> SpecialEventT:
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
            data.tick, timestamp, data.sustain, proximal_bpm_event_index=proximal_bpm_event_index
        )

    def tick_is_in_event(self, tick: int) -> bool:
        return self.tick <= tick and not self.tick_is_after_event(tick)

    def tick_is_after_event(self, tick: int) -> bool:
        return tick >= self.end_tick

    def __str__(self) -> str:  # pragma: no cover
        to_join = [super().__str__()]
        to_join.append(f": sustain={self.sustain}")
        return "".join(to_join)

    ParsedDataT = TypeVar("ParsedDataT", bound="ParsedData")

    @dataclasses.dataclass
    class ParsedData(Event.ParsedData):
        tick: int
        sustain: int

        _regex: ClassVar[str]
        _regex_prog: ClassVar[Pattern[str]]

        # Match 1: Tick
        # Match 2: Sustain (ticks)
        _regex_template: Final[str] = r"^\s*?(\d+?) = S {} (\d+?)\s*?$"
        _index_regex: ClassVar[str]

        @classmethod
        def from_chart_line(
            cls: Type[SpecialEvent.ParsedDataT], line: str
        ) -> SpecialEvent.ParsedDataT:
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
            tick, sustain = int(m.group(1)), int(m.group(2))
            return cls(tick, sustain)


@typing.final
class StarPowerEvent(SpecialEvent):
    """An event representing star power starting at some tick and lasting for some duration."""

    @typing.final
    @dataclasses.dataclass
    class ParsedData(SpecialEvent.ParsedData):
        _index_regex = r"2"
        _regex = SpecialEvent.ParsedData._regex_template.format(_index_regex)
        _regex_prog = re.compile(_regex)


# TODO: Support S 0 ## and S 1 ## (GH1/2 Co-op)


# TODO: Support S 64 ## (Rock Band drum fills)
