"""For representing the data related to a single (instrument, difficulty) pair.

You should not need to create any of this module's objects manually; please instead create a
:class:`~chartparse.chart.Chart` and inspect its attributes via that object.

.. _Google Python Style Guide:
    http://google.github.io/styleguide/pyguide.html

"""

from __future__ import annotations

import collections
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
from chartparse.datastructures import ImmutableSortedList
from chartparse.event import Event, TimestampAtTickSupporter
from chartparse.exceptions import RegexNotMatchError
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


@typing.final
class InstrumentTrack(DictPropertiesEqMixin, DictReprTruncatedSequencesMixin):
    """All of the instrument-related events for one (instrument, difficulty) pair."""

    resolution: Final[int]
    """The number of ticks for which a quarter note lasts."""

    instrument: Final[Instrument]
    """The instrument to which this track corresponds."""

    difficulty: Final[Difficulty]
    """This track's difficulty setting."""

    section_name: Final[str]
    """The concatenation of this track's difficulty and instrument (in that order)."""

    note_events: Final[Sequence[NoteEvent]]
    """An (instrument, difficulty) pair's ``NoteEvent`` objects."""

    star_power_events: Final[Sequence[StarPowerEvent]]
    """An (instrument, difficulty) pair's ``StarPowerEvent`` objects."""

    # TODO: Make this optional? What if there are no notes?
    _last_note_timestamp: datetime.timedelta
    """The timestamp at which the :attr:`~chartparse.instrument.NoteEvent.sustain` value of the
    last :class:`~chartparse.instrument.NoteEvent` ends.

    If that event has no :attr:`~chartparse.instrument.NoteEvent.sustain` value, then this is just
    the timestamp of that :class:`~chartparse.instrument.NoteEvent`.

    This is not set in ``__init__``; it must be set via ``Chart._populate_last_note_timestamp``.
    """

    _min_note_instrument_track_index = 0
    _max_note_instrument_track_index = 4
    _open_instrument_track_index = 7
    _forced_instrument_track_index = 5
    _tap_instrument_track_index = 6

    _unhandled_note_track_index_log_msg_tmpl: ClassVar[str] = "unhandled note track index {}"

    def __init__(
        self,
        resolution: int,
        instrument: Instrument,
        difficulty: Difficulty,
        note_events: Sequence[NoteEvent],
        star_power_events: Sequence[StarPowerEvent],
    ) -> None:
        """Instantiates all instance attributes."""
        if resolution <= 0:
            raise ValueError(f"resolution ({resolution}) must be positive")

        self.resolution = resolution
        self.instrument = instrument
        self.difficulty = difficulty
        self.note_events = note_events
        self.star_power_events = star_power_events
        self.section_name = difficulty.value + instrument.value
        self._populate_star_power_data()

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

        note_events = cls._parse_note_events_from_chart_lines(iterator_getter(), tatter)
        star_power_events: ImmutableSortedList[
            StarPowerEvent
        ] = chartparse.track.parse_events_from_chart_lines(
            iterator_getter(),
            StarPowerEvent.from_chart_line,
            tatter,
        )
        return cls(tatter.resolution, instrument, difficulty, note_events, star_power_events)

    def __str__(self) -> str:  # pragma: no cover
        return (
            f"{type(self).__name__}"
            f"(instrument: {self.instrument}, "
            f"difficulty: {self.difficulty}, "
            f"len(note_events): {len(self.note_events)}, "
            f"len(star_power_events): {len(self.star_power_events)})"
        )

    # TODO: Granularize this function into multiple functions for better profiling and readability.
    @classmethod
    def _parse_note_events_from_chart_lines(
        cls,
        chart_lines: Iterable[str],
        tatter: TimestampAtTickSupporter,
    ) -> ImmutableSortedList[NoteEvent]:
        # TODO: Use regular dicts here; this function is a very tight loop so
        # they're probably faster.
        tick_to_note_array: collections.defaultdict[int, bytearray] = collections.defaultdict(
            lambda: bytearray(5)
        )
        tick_to_sustain_list: collections.defaultdict[
            int, list[Optional[int]]
        ] = collections.defaultdict(lambda: [None] * 5)
        tick_to_is_tap = collections.defaultdict(bool)
        tick_to_is_forced = collections.defaultdict(bool)
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
                tick_to_note_array[tick][note_index] = 1
                tick_to_sustain_list[tick][note_index] = sustain
            elif note_index == InstrumentTrack._open_instrument_track_index:
                # Because `tick_to_note_array` is a defaultdict, simply accessing it at `tick` is
                # sufficient to conjure a bytearray representing an open note.
                tick_to_note_array[tick]
                tick_to_sustain_list[tick]
            elif note_index == InstrumentTrack._tap_instrument_track_index:
                tick_to_is_tap[tick] = True
            elif note_index == InstrumentTrack._forced_instrument_track_index:
                tick_to_is_forced[tick] = True
            else:  # pragma: no cover
                # TODO: Once _parse_note_events_from_chart_lines has its own unit tests, cover this
                # branch.
                logger.warning(cls._unhandled_note_track_index_log_msg_tmpl.format(note_index))
                continue

        start_bpm_event_index = 0
        events: list[NoteEvent] = []
        for tick in sorted(tick_to_note_array.keys()):
            note = Note(tick_to_note_array[tick])
            timestamp, start_bpm_event_index = tatter.timestamp_at_tick(
                tick, start_bpm_event_index=start_bpm_event_index
            )
            previous_event = events[-1] if events else None
            hopo_state = NoteEvent.compute_hopo_state(
                tatter.resolution,
                tick,
                note,
                tick_to_is_tap[tick],
                tick_to_is_forced[tick],
                previous_event,
            )
            event = NoteEvent(
                tick,
                timestamp,
                note,
                hopo_state,
                sustain=tuple(tick_to_sustain_list[tick]),
                proximal_bpm_event_idx=start_bpm_event_index,
            )
            events.append(event)
        return ImmutableSortedList(events, key=lambda e: e.tick)

    def _populate_star_power_data(self) -> None:
        num_notes = len(self.note_events)

        note_idx_to_star_power_idx = dict()
        note_idx = 0
        for star_power_idx, star_power_event in enumerate(self.star_power_events):
            star_power_start_tick = star_power_event.tick
            star_power_end_tick = star_power_start_tick + star_power_event.sustain

            # Seek the first note after this star power phrase.
            while note_idx < num_notes:
                note = self.note_events[note_idx]
                if note.tick >= star_power_end_tick:
                    break
                if star_power_start_tick <= note.tick:
                    note_idx_to_star_power_idx[note_idx] = star_power_idx
                note_idx += 1

        for note_idx, note_event in enumerate(self.note_events):
            star_power_index_of_note = note_idx_to_star_power_idx.get(note_idx, None)
            if star_power_index_of_note is None:
                continue
            note_event.star_power_data = StarPowerData(star_power_index_of_note)


@typing.final
@dataclass
class StarPowerData(DictPropertiesEqMixin):
    """Star power related info for a :class:`~chartparse.instrument.NoteEvent`."""

    # This is conceptually Final, but annotating it as such confuses mypy into thinking it should
    # be ClassVar.
    star_power_event_idx: int


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

    hopo_state: Final[HOPOState]
    """Whether the note is a strum, a HOPO, or a tap note."""

    # TODO: Make this final.
    star_power_data: Optional[StarPowerData]
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
        note: Note,
        hopo_state: HOPOState,
        sustain: ComplexNoteSustainT = 0,
        star_power_data: Optional[StarPowerData] = None,
        proximal_bpm_event_idx: int = 0,
    ) -> None:
        super().__init__(tick, timestamp, proximal_bpm_event_idx=proximal_bpm_event_idx)
        self.note = note
        self.hopo_state = hopo_state
        self.sustain = self._refine_sustain(sustain)
        self.star_power_data = star_power_data

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
    def compute_hopo_state(
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

    @functools.cached_property
    def longest_sustain(self) -> int:
        if isinstance(self.sustain, int):
            return self.sustain
        elif isinstance(self.sustain, tuple):
            if all(s is None for s in self.sustain):
                raise ValueError("all sustain values are `None`")
            return max(s for s in self.sustain if s is not None)
        else:
            raise RuntimeError(
                f"sustain {self.sustain} must be type list, or int."
            )  # pragma: no cover


SpecialEventT = TypeVar("SpecialEventT", bound="SpecialEvent")


class SpecialEvent(Event):
    """Provides a regex template for parsing 'S' style chart lines.

    This is typically used only as a base class for more specialized subclasses.

    Attributes:
        sustain: The number of ticks for which this event is sustained. This event does _not_
            overlap events at ``tick + sustain``; it ends immediately before that tick.
    """

    # Match 1: Tick
    # Match 2: Sustain (ticks)
    _regex_template: Final[str] = r"^\s*?(\d+?) = S {} (\d+?)\s*?$"

    # These should be set by a subclass.
    _regex: str
    _regex_prog: Pattern[str]

    def __init__(
        self,
        tick: int,
        timestamp: datetime.timedelta,
        sustain: int,
        proximal_bpm_event_idx: int = 0,
    ) -> None:
        super().__init__(tick, timestamp, proximal_bpm_event_idx=proximal_bpm_event_idx)
        self.sustain = sustain

    @classmethod
    def from_chart_line(
        cls: Type[SpecialEventT],
        line: str,
        prev_event: Optional[SpecialEventT],
        tatter: TimestampAtTickSupporter,
    ) -> SpecialEventT:
        """Attempt to obtain an instance of this object from a string.

        Args:
            line: Most likely a line from a Moonscraper ``.chart``.
            prev_event: The ``SpecialEvent`` with the greatest ``tick`` value less than that of
                this event. If this is ``None``, then this must be the first ``SpecialEvent``.
            tatter: An object that can be used to get a timestamp at a particular tick.

        Returns:
            An an instance of this object parsed from ``line``.

        Raises:
            RegexNotMatchError: If the mixed-into class' ``_regex`` does not match ``line``.
        """

        m = cls._regex_prog.match(line)
        if not m:
            raise RegexNotMatchError(cls._regex, line)
        tick, sustain = int(m.group(1)), int(m.group(2))
        timestamp, proximal_bpm_event_idx = cls.calculate_timestamp(tick, prev_event, tatter)
        return cls(tick, timestamp, sustain, proximal_bpm_event_idx=proximal_bpm_event_idx)

    def __str__(self) -> str:  # pragma: no cover
        to_join = [super().__str__()]
        to_join.append(f": sustain={self.sustain}")
        return "".join(to_join)


@typing.final
class StarPowerEvent(SpecialEvent):
    """An event representing star power starting at some tick and lasting for some duration."""

    _regex = SpecialEvent._regex_template.format(r"2")
    _regex_prog = re.compile(_regex)


# TODO: Support S 0 ## and S 1 ## (GH1/2 Co-op)


# TODO: Support S 64 ## (Rock Band drum fills)
