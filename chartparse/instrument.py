"""For representing the data related to a single (instrument, difficulty) pair.

You should not need to create any of this module's objects manually; please instead create a
:class:`~chartparse.chart.Chart` and inspect its attributes via that object.

.. _Google Python Style Guide:
    http://google.github.io/styleguide/pyguide.html

"""

from __future__ import annotations

import dataclasses
import datetime
import enum
import functools
import logging
import re
import typing as typ
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from enum import Enum

import chartparse.tick
import chartparse.track
from chartparse.datastructures import ImmutableSortedList
from chartparse.event import Event, TimestampAtTickSupporter
from chartparse.exceptions import ProgrammerError, RegexNotMatchError
from chartparse.tick import NoteDuration
from chartparse.util import (
    AllValuesGettableEnum,
    DictPropertiesEqMixin,
    DictReprTruncatedSequencesMixin,
)

logger = logging.getLogger(__name__)


@typ.final
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


@typ.final
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


NoteT = typ.TypeVar("NoteT", bound="Note")


@typ.final
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


@typ.final
@functools.total_ordering
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

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented  # pragma: no cover


# TODO: create newtype (?) for bytearray for note array.


@typ.final
class InstrumentTrack(DictPropertiesEqMixin, DictReprTruncatedSequencesMixin):
    """All of the instrument-related events for one (instrument, difficulty) pair."""

    resolution: typ.Final[int]
    """The number of ticks for which a quarter note lasts."""

    instrument: typ.Final[Instrument]
    """The instrument to which this track corresponds."""

    difficulty: typ.Final[Difficulty]
    """This track's difficulty setting."""

    # TODO: All of these sequences of events should probably be individual objects so things like
    # _last_note_timestamp can live more tightly coupled to the actual events.
    note_events: typ.Final[Sequence[NoteEvent]]
    """An (instrument, difficulty) pair's ``NoteEvent`` objects."""

    star_power_events: typ.Final[ImmutableSortedList[StarPowerEvent]]
    """An (instrument, difficulty) pair's ``StarPowerEvent`` objects."""

    _min_note_instrument_track_index = 0
    _max_note_instrument_track_index = 4
    _open_instrument_track_index = 7
    _forced_instrument_track_index = 5
    _tap_instrument_track_index = 6

    _SelfT = typ.TypeVar("_SelfT", bound="InstrumentTrack")

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
    def last_note_end_timestamp(self) -> datetime.timedelta | None:
        """The timestamp at which the :attr:`~chartparse.instrument.NoteEvent.sustain` value of the
        last :class:`~chartparse.instrument.NoteEvent` ends.

        This is ``None`` iff the track has no notes.
        """
        if not self.note_events:
            return None
        return max(self.note_events, key=lambda e: e.end_timestamp).end_timestamp

    @classmethod
    def from_chart_lines(
        cls: type[_SelfT],
        instrument: Instrument,
        difficulty: Difficulty,
        lines: Iterable[str],
        tatter: TimestampAtTickSupporter,
    ) -> _SelfT:
        """Initializes instance attributes by parsing an iterable of strings.

        Args:
            instrument: The instrument to which this track corresponds.
            difficulty: This track's difficulty setting.
            lines: An iterable of strings most likely from a Moonscraper ``.chart``.
            tatter: An object that can be used to get a timestamp at a particular tick.

        Returns:
            An ``InstrumentTrack`` parsed from ``line``.
        """

        note_data, star_power_data = cls._parse_data_from_chart_lines(lines)
        star_power_events = chartparse.track.build_events_from_data(
            star_power_data,
            StarPowerEvent.from_parsed_data,
            tatter,
        )
        note_events = cls._build_note_events_from_data(note_data, star_power_events, tatter)
        return cls(tatter.resolution, instrument, difficulty, note_events, star_power_events)

    @classmethod
    def _parse_data_from_chart_lines(
        cls: type[_SelfT],
        lines: Iterable[str],
    ) -> tuple[list[NoteEvent.ParsedData], list[StarPowerEvent.ParsedData]]:
        parsed_data = chartparse.track.parse_data_from_chart_lines(
            (NoteEvent.ParsedData, StarPowerEvent.ParsedData), lines
        )
        note_data = typ.cast(
            list[NoteEvent.ParsedData],
            parsed_data[NoteEvent.ParsedData],
        )
        star_power_data = typ.cast(
            list[StarPowerEvent.ParsedData],
            parsed_data[StarPowerEvent.ParsedData],
        )
        return note_data, star_power_data

    def __str__(self) -> str:  # pragma: no cover
        return (
            f"{type(self).__name__}"
            f"(instrument: {self.instrument}, "
            f"difficulty: {self.difficulty}, "
            f"len(note_events): {len(self.note_events)}, "
            f"len(star_power_events): {len(self.star_power_events)})"
        )

    @classmethod
    def _build_note_events_from_data(
        cls,
        datas: Iterable[NoteEvent.ParsedData],
        star_power_events: ImmutableSortedList[StarPowerEvent],
        tatter: TimestampAtTickSupporter,
    ) -> ImmutableSortedList[NoteEvent]:
        proximal_bpm_event_index = 0
        star_power_event_index = 0
        events: list[NoteEvent] = []
        for data in datas:
            previous_event = events[-1] if events else None
            event, proximal_bpm_event_index, star_power_event_index = NoteEvent.from_parsed_data(
                data,
                previous_event,
                star_power_events,
                tatter,
                proximal_bpm_event_index=proximal_bpm_event_index,
                star_power_event_index=star_power_event_index,
            )
            events.append(event)

        # TODO: Is this still already sorted? Can we perhaps define `datas` further
        # up the call hierarchy as an ImmutableSortedList, so it's straightforward?
        return ImmutableSortedList(events, already_sorted=True)


@typ.final
@dataclass
class StarPowerData(DictPropertiesEqMixin):
    """Star power related info for a :class:`~chartparse.instrument.NoteEvent`."""

    # This is conceptually Final, but annotating it as such confuses mypy into thinking it should
    # be ClassVar.
    star_power_event_index: int


# TODO: See what happens if we specify five Optional[int]s, rather than ...
SustainTupleT = tuple[int | None, ...]
"""A 5-element tuple representing the sustain value of each note lane for nonuniform sustains.

An element is ``None`` if and only if the corresponding note lane is inactive. If an element is
``0``, then there must be at least one other non-``0``, non-``None`` element; this is because that
``0`` element represents an unsustained note in unison with a sustained note.
"""

SustainListT = list[int | None]
"""A 5-element tuple representing the sustain value of each note lane for nonuniform sustains.

An element is ``None`` if and only if the corresponding note lane is inactive. If an element is
``0``, then there must be at least one other non-``0``, non-``None`` element; this is because that
``0`` element represents an unsustained note in unison with a sustained note.
"""

# TODO: Migrate simple Unions to use 3.10 pipe syntax.
ComplexSustainT = int | SustainTupleT
"""An immutable sustain value representing multiple coinciding notes with different sustain values.

If this value is an ``int``, it means that all active note lanes at this tick value are sustained
for the same number of ticks. If this value is ``0``, then none of the note lanes are active.
"""

ComplexSustainListT = int | SustainListT
"""A mutable sustain value representing multiple coinciding notes with different sustain values.

If this value is an ``int``, it means that all active note lanes at this tick value are sustained
for the same number of ticks. If this value is ``[None, None, None, None, None]``, then none of the
note lanes are active.
"""


@typ.final
@enum.unique
class HOPOState(Enum):
    """The manner in which a :class:`~chartparse.instrument.NoteEvent` can/must be hit."""

    STRUM = 0
    HOPO = 1
    TAP = 2


NoteEventT = typ.TypeVar("NoteEventT", bound="NoteEvent")


@typ.final
class NoteEvent(Event):
    """An event representing all of the notes at a particular tick.

    A note event's ``str`` representation looks like this::

        NoteEvent(t@0000816 0:00:02.093750): sustain=0: Note.Y [flags=H]

    This event occurs at tick 816 and timestamp 0:00:02.093750. It is not sustained. It is yellow.
    It is a HOPO. Other valid flags are ``T`` (for "tap") and ``S`` (for "strum").

    """

    note: typ.Final[Note]
    """The note lane(s) that are active."""

    sustain: typ.Final[ComplexSustainT]
    """Information about this note event's sustain value."""

    end_timestamp: typ.Final[datetime.timedelta]
    """The timestamp at which this note ends."""

    hopo_state: typ.Final[HOPOState]
    """Whether the note is a strum, a HOPO, or a tap note."""

    star_power_data: typ.Final[StarPowerData | None]
    """Information associated with star power for this note.

    If this is ``None``, then the note is not a star power note.
    """

    def __init__(
        self,
        tick: int,
        timestamp: datetime.timedelta,
        end_timestamp: datetime.timedelta,
        note: Note,
        hopo_state: HOPOState,
        sustain: ComplexSustainT = 0,
        star_power_data: StarPowerData | None = None,
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
        """The length of the longest sustained note in this event.

        It's possible for different notes to have different sustain values at the same tick.
        """
        return self._longest_sustain(self.sustain)

    @staticmethod
    def _longest_sustain(sustain: ComplexSustainT) -> int:
        if isinstance(sustain, int):
            return sustain
        elif isinstance(sustain, tuple):
            if all(s is None for s in sustain):
                raise ValueError("all sustain values are `None`")
            return max(s for s in sustain if s is not None)
        else:
            raise ProgrammerError  # pragma: no cover

    @functools.cached_property
    def end_tick(self) -> int:
        """The tick immediately after this note ends."""
        return self._end_tick(self.tick, self.longest_sustain)

    @staticmethod
    def _end_tick(tick: int, sustain: int) -> int:
        return tick + sustain

    @classmethod
    def from_parsed_data(
        cls: type[NoteEventT],
        data: NoteEvent.ParsedData,
        prev_event: NoteEvent | None,
        star_power_events: ImmutableSortedList[StarPowerEvent],
        tatter: TimestampAtTickSupporter,
        proximal_bpm_event_index: int = 0,
        star_power_event_index: int = 0,
    ) -> tuple[NoteEventT, int, int]:
        note = Note(data.note_array)

        timestamp, proximal_bpm_event_index = tatter.timestamp_at_tick(
            data.tick, proximal_bpm_event_index=proximal_bpm_event_index
        )

        hopo_state = NoteEvent._compute_hopo_state(
            tatter.resolution,
            data.tick,
            note,
            data.is_tap,
            data.is_forced,
            prev_event,
        )

        star_power_data, star_power_event_index = NoteEvent._compute_star_power_data(
            data.tick, star_power_events, proximal_star_power_event_index=star_power_event_index
        )

        sustain = data.immutable_sustain
        if sustain is None:
            raise ValueError("sustain must not be None")

        longest_sustain = cls._longest_sustain(sustain)
        end_tick = cls._end_tick(data.tick, longest_sustain)
        end_timestamp, _ = tatter.timestamp_at_tick(
            end_tick, proximal_bpm_event_index=proximal_bpm_event_index
        )

        event = cls(
            data.tick,
            timestamp,
            end_timestamp,
            note,
            hopo_state,
            sustain=sustain,
            star_power_data=star_power_data,
            proximal_bpm_event_index=proximal_bpm_event_index,
        )
        return event, proximal_bpm_event_index, star_power_event_index

    @staticmethod
    @functools.lru_cache
    # sustains tend to have similar-ish values, so lru_cache should help out here.
    def _refine_sustain(sustain: ComplexSustainT) -> ComplexSustainT:
        if isinstance(sustain, int):
            return sustain
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
        previous: NoteEvent | None,
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
    ) -> tuple[StarPowerData | None, int]:
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

    ParsedDataT = typ.TypeVar("ParsedDataT", bound="ParsedData")

    @dataclasses.dataclass(kw_only=True)
    class ParsedData(Event.CoalescableParsedData[ParsedDataT]):
        note_array: bytearray
        """The note lane(s) active in the event represented by this data.

        This is basically a mutable :class:`~chartparse.instrument.Note`, since this type is
        coalescable.
        """

        sustain: ComplexSustainListT | None
        """The durations in ticks of the active lanes in the event represented by this data."""

        is_tap: bool = False
        """Whether the note in this event is a tap note."""

        is_forced: bool = False
        """Whether the note in this event is a forced HOPO/strum."""

        # This regex matches a single "N" line within a instrument track section,
        # but this class should be used to represent all of the notes at a
        # particular tick. This means that you might need to consolidate multiple
        # "N" lines into a single NoteEvent, e.g. for chords.
        # Match 1: Tick
        # Match 2: Note index
        # Match 3: Sustain (ticks)
        _regex: typ.Final[str] = r"^\s*?(\d+?) = N ([0-7]) (\d+?)\s*?$"
        _regex_prog: typ.Final[typ.Pattern[str]] = re.compile(_regex)

        _unhandled_note_track_index_log_msg_tmpl: typ.Final[
            str
        ] = "unhandled note track index {} at tick {}"

        # _SelfT = typ.TypeVar("_SelfT", bound="NoteEvent.ParsedData")

        @functools.cached_property
        def immutable_sustain(self) -> ComplexSustainT | None:
            """The value of ``sustain``, but converted to an immutable type if necessary."""
            if self.sustain is None:
                return None
            elif isinstance(self.sustain, int):
                return self.sustain
            else:
                return tuple(self.sustain)

        @classmethod
        def from_chart_line(cls: type[NoteEvent.ParsedDataT], line: str) -> NoteEvent.ParsedDataT:
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
            parsed_tick, parsed_note_index, parsed_sustain = (
                int(m.group(1)),
                int(m.group(2)),
                int(m.group(3)),
            )
            note_track_index = NoteTrackIndex(parsed_note_index)

            note_array = bytearray(5)
            sustain: ComplexSustainListT | None = None
            is_forced = False
            is_tap = False
            # type ignored here because mypy does not understand that this enum
            # uses functools.total_ordering.
            if NoteTrackIndex.GREEN <= note_track_index <= NoteTrackIndex.ORANGE:  # type: ignore
                note_array[parsed_note_index] = 1
                sustain = [None] * 5
                sustain[parsed_note_index] = parsed_sustain
            elif note_track_index == NoteTrackIndex.OPEN:
                sustain = parsed_sustain
            elif note_track_index == NoteTrackIndex.FORCED:
                is_forced = True
            elif note_track_index == NoteTrackIndex.TAP:
                is_tap = True
            else:  # pragma: no cover
                # Not reachable if regex does its job.
                logger.warning(
                    cls._unhandled_note_track_index_log_msg_tmpl.format(
                        note_track_index, parsed_tick
                    )
                )
            return cls(
                tick=parsed_tick,
                note_array=note_array,
                sustain=sustain,
                is_forced=is_forced,
                is_tap=is_tap,
            )

        # TODO: This can be optimized by instead creating a class to represent
        # the data from a single line. i.e. they can specify:
        # - exactly one of the six notes, or a force or tap flag.
        # - and exactly one Optional sustain value.
        def coalesce_from_other(self, other: NoteEvent.ParsedDataT) -> None:
            """Merge the contents of another data into this one.

            Args:
                other: another subclass of :class:`~chartparse.event.Event.ParsedData` of the same
                type.

            Raises:
                ValueError: if this data or the other data has an ``int`` typed ``sustain``. This
                    is because an ``int`` value in this field means that it represents an open
                    note, and it is nonsensical for an open note to overlap another concrete note.
            """
            if other.sustain is not None:
                if self.sustain is None:
                    self.sustain = other.sustain
                elif isinstance(self.sustain, int) or isinstance(other.sustain, int):
                    # both not None after the first branch
                    raise ValueError("open note cannot coincide with other notes")
                else:
                    # merge first present sustain value from ``other``
                    for i, s in enumerate(other.sustain):
                        if s is not None:
                            self.sustain[i] = s

            # merge first present note value from ``other``
            for i, n in enumerate(other.note_array):
                if n:
                    self.note_array[i] = 1

            self.is_forced = self.is_forced or other.is_forced
            self.is_tap = self.is_tap or other.is_tap


class SpecialEvent(Event):
    """Provides a regex template for parsing 'S' style chart lines.

    This is typically used only as a base class for more specialized subclasses.
    """

    sustain: typ.Final[int]
    """The number of ticks for which this event is sustained.

    This event does _not_ overlap events at ``tick + sustain``; it ends immediately before that
    tick.
    """

    _SelfT = typ.TypeVar("_SelfT", bound="SpecialEvent")

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
        """The tick immediately after this event ends."""
        return self.tick + self.sustain

    @classmethod
    def from_parsed_data(
        cls: type[_SelfT],
        data: SpecialEvent.ParsedData,
        prev_event: _SelfT | None,
        tatter: TimestampAtTickSupporter,
    ) -> _SelfT:
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

    @dataclasses.dataclass(kw_only=True)
    class ParsedData(Event.ParsedData):
        sustain: int
        """The duration in ticks of the event represented by this data."""

        _regex: typ.ClassVar[str]
        _regex_prog: typ.ClassVar[typ.Pattern[str]]

        # Match 1: Tick
        # Match 2: Sustain (ticks)
        _regex_template: typ.Final[str] = r"^\s*?(\d+?) = S {} (\d+?)\s*?$"
        _index_regex: typ.ClassVar[str]

        _SelfT = typ.TypeVar("_SelfT", bound="SpecialEvent.ParsedData")

        @classmethod
        def from_chart_line(cls: type[_SelfT], line: str) -> _SelfT:
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
            return cls(tick=tick, sustain=sustain)


@typ.final
class StarPowerEvent(SpecialEvent):
    """An event representing star power starting at some tick and lasting for some duration."""

    @typ.final
    @dataclasses.dataclass(kw_only=True)
    class ParsedData(SpecialEvent.ParsedData):
        _index_regex = r"2"
        _regex = SpecialEvent.ParsedData._regex_template.format(_index_regex)
        _regex_prog = re.compile(_regex)


# TODO: Support S 0 ## and S 1 ## (GH1/2 Co-op)


# TODO: Support S 64 ## (Rock Band drum fills)


# TODO: Support E textherewithoutspaces ("track events") within InstrumentTracks.
