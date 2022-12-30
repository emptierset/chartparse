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
from enum import Enum

import chartparse.tick
import chartparse.track
from chartparse.event import Event, TimestampAtTickSupporter
from chartparse.exceptions import RegexNotMatchError
from chartparse.tick import NoteDuration
from chartparse.util import (
    AllValuesGettableEnum,
    DictPropertiesEqMixin,
    DictReprMixin,
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


@typ.final
class Note(Enum):
    """The note lane(s) to which a :class:`~chartparse.instrument.NoteEvent` corresponds."""

    _Self = typ.TypeVar("_Self", bound="Note")

    # TODO: optimization: Are bytearrays really better than plain tuples here?
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

    @functools.lru_cache
    def is_chord(self):
        """Returns whether this ``Note`` has multiple active lanes."""

        return sum(self.value) > 1

    @classmethod
    def from_parsed_data(
        cls: type[_Self], data: NoteEvent.ParsedData | Sequence[NoteEvent.ParsedData]
    ) -> _Self:
        """Returns the ``Note`` represented by one or more ``NoteEvent.ParsedData``s.

        Args:
            data: The data or datas whose note track indices should be examined.

        Returns:
            The ``Note`` represented by ``datas``.
        """
        datas = data if isinstance(data, Sequence) else [data]

        arr = bytearray(5)
        for d in datas:
            try:
                arr[d.note_track_index.value] = 1
            except IndexError:
                pass
        return cls(arr)


@typ.final
@functools.total_ordering
class NoteTrackIndex(AllValuesGettableEnum):
    """The integer in a line in a Moonscraper ``.chart`` file's instrument track."""

    _Self = typ.TypeVar("_Self", bound="NoteTrackIndex")

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

    @functools.lru_cache
    def is_5_note(self) -> bool:
        """Returns whether this is one of the five "normal" note indices."""
        return NoteTrackIndex.G.value <= self.value <= NoteTrackIndex.O.value


@typ.final
class InstrumentTrack(DictPropertiesEqMixin, DictReprTruncatedSequencesMixin):
    """All of the instrument-related events for one (instrument, difficulty) pair."""

    _Self = typ.TypeVar("_Self", bound="InstrumentTrack")

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

    star_power_events: typ.Final[Sequence[StarPowerEvent]]
    """An (instrument, difficulty) pair's ``StarPowerEvent`` objects."""

    track_events: typ.Final[Sequence[TrackEvent]]
    """An (instrument, difficulty) pair's ``TrackEvent`` objects."""

    _min_note_instrument_track_index = 0
    _max_note_instrument_track_index = 4
    _open_instrument_track_index = 7
    _forced_instrument_track_index = 5
    _tap_instrument_track_index = 6

    def __init__(
        self,
        resolution: int,
        instrument: Instrument,
        difficulty: Difficulty,
        note_events: Sequence[NoteEvent],
        star_power_events: Sequence[StarPowerEvent],
        track_events: Sequence[TrackEvent],
    ) -> None:
        """Instantiates all instance attributes."""
        if resolution <= 0:
            raise ValueError(f"resolution ({resolution}) must be positive")

        self.resolution = resolution
        self.instrument = instrument
        self.difficulty = difficulty
        self.note_events = note_events
        self.star_power_events = star_power_events
        self.track_events = track_events

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
        cls: type[_Self],
        instrument: Instrument,
        difficulty: Difficulty,
        lines: Iterable[str],
        tatter: TimestampAtTickSupporter,
    ) -> _Self:
        """Initializes instance attributes by parsing an iterable of strings.

        Args:
            instrument: The instrument to which this track corresponds.
            difficulty: This track's difficulty setting.
            lines: An iterable of strings most likely from a Moonscraper ``.chart``.
            tatter: An object that can be used to get a timestamp at a particular tick.

        Returns:
            An ``InstrumentTrack`` parsed from ``line``.
        """

        note_data, star_power_data, track_data = cls._parse_data_from_chart_lines(lines)
        star_power_events = chartparse.track.build_events_from_data(
            star_power_data,
            StarPowerEvent.from_parsed_data,
            tatter,
        )
        track_events = chartparse.track.build_events_from_data(
            track_data,
            TrackEvent.from_parsed_data,
            tatter,
        )
        note_events = cls._build_note_events_from_data(note_data, star_power_events, tatter)
        return cls(
            tatter.resolution, instrument, difficulty, note_events, star_power_events, track_events
        )

    @classmethod
    def _parse_data_from_chart_lines(
        cls: type[_Self],
        lines: Iterable[str],
    ) -> tuple[
        list[NoteEvent.ParsedData], list[StarPowerEvent.ParsedData], list[TrackEvent.ParsedData]
    ]:
        parsed_data = chartparse.track.parse_data_from_chart_lines(
            (NoteEvent.ParsedData, StarPowerEvent.ParsedData, TrackEvent.ParsedData), lines
        )
        return (
            parsed_data[NoteEvent.ParsedData],
            parsed_data[StarPowerEvent.ParsedData],
            parsed_data[TrackEvent.ParsedData],
        )

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
        datas: Sequence[NoteEvent.ParsedData],
        star_power_events: Sequence[StarPowerEvent],
        tatter: TimestampAtTickSupporter,
    ) -> list[NoteEvent]:
        proximal_bpm_event_index = 0
        star_power_event_index = 0
        events: list[NoteEvent] = []
        i = 0
        num_datas = len(datas)
        while i < num_datas:
            previous_event = events[-1] if events else None

            # Find all datas with the same tick value. Because the input is expected to be sorted
            # by tick value, these such datas should always be in a contiguous block.
            left = i
            while i + 1 < num_datas and datas[i + 1].tick == datas[i].tick:
                i += 1
            right = i + 1

            event, proximal_bpm_event_index, star_power_event_index = NoteEvent.from_parsed_data(
                datas[left:right],
                previous_event,
                star_power_events,
                tatter,
                proximal_bpm_event_index=proximal_bpm_event_index,
                star_power_event_index=star_power_event_index,
            )
            events.append(event)
            i += 1

        return events


@typ.final
@dataclasses.dataclass(frozen=True)
class StarPowerData(DictPropertiesEqMixin):
    """Star power related info for a :class:`~chartparse.instrument.NoteEvent`."""

    # This is conceptually Final, but annotating it as such confuses mypy into thinking it should
    # be ClassVar.
    star_power_event_index: int


_SustainList = typ.NewType("_SustainList", list[int | None])
"""A mutable SustainTuple."""

SustainTuple = typ.NewType(
    "SustainTuple", tuple[int | None, int | None, int | None, int | None, int | None]
)
"""A 5-element tuple representing the sustain value of each note lane for nonuniform sustains.

An element is ``None`` if and only if the corresponding note lane is inactive. If an element is
``0``, then there will be at least one other non-``0``, non-``None`` element; this is because that
``0`` element represents an unsustained note in unison with a sustained note.
"""

ComplexSustain = int | SustainTuple
"""An sustain value representing multiple coinciding notes with different sustain values.

If this value is an ``int``, it means that all active note lanes at this tick value are sustained
for the same number of ticks. If this value is ``0``, then none of the note lanes are active.
"""


def complex_sustain_from_parsed_data(
    data: NoteEvent.ParsedData | Sequence[NoteEvent.ParsedData],
) -> ComplexSustain:
    """Returns a ComplexSustain incorporating multiple ParsedDatas.

    If ``data`` has multiple elements, one or more of which correspond to open notes, this
    function's behavior is undefined.

    Args:
        data: The data or datas whose sustain values should be coalesced.

    Returns:
        The sustain values of ``datas`` coalesced into a single ComplexSustain.
    """
    datas = data if isinstance(data, Sequence) else [data]

    if datas[0].note_track_index == NoteTrackIndex.OPEN:
        return datas[0].sustain

    sustain_list = _SustainList([None] * 5)
    for d in filter(lambda d: d.note_track_index.is_5_note(), datas):
        sustain_list[d.note_track_index.value] = d.sustain

    if all(s is None for s in sustain_list):
        return 0

    first_non_none_sustain = next(s for s in sustain_list if s is not None)
    if all(d is None or d == first_non_none_sustain for d in sustain_list):
        return first_non_none_sustain

    return typ.cast(ComplexSustain, tuple(sustain_list))


@typ.final
@enum.unique
class HOPOState(Enum):
    """The manner in which a :class:`~chartparse.instrument.NoteEvent` can/must be hit."""

    STRUM = 0
    HOPO = 1
    TAP = 2


@typ.final
class NoteEvent(Event):
    """An event representing all of the notes at a particular tick.

    A note event's ``str`` representation looks like this::

        NoteEvent(t@0000816 0:00:02.093750): sustain=0: Note.Y [flags=H]

    This event occurs at tick 816 and timestamp 0:00:02.093750. It is not sustained. It is yellow.
    It is a HOPO. Other valid flags are ``T`` (for "tap") and ``S`` (for "strum").

    """

    _Self = typ.TypeVar("_Self", bound="NoteEvent")

    note: typ.Final[Note]
    """The note lane(s) that are active."""

    sustain: typ.Final[ComplexSustain]
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
        sustain: ComplexSustain = 0,
        star_power_data: StarPowerData | None = None,
        proximal_bpm_event_index: int = 0,
    ) -> None:
        super().__init__(tick, timestamp, proximal_bpm_event_index=proximal_bpm_event_index)
        self.end_timestamp = end_timestamp
        self.note = note
        self.hopo_state = hopo_state
        self.sustain = sustain
        self.star_power_data = star_power_data

    @functools.cached_property
    def longest_sustain(self) -> int:
        """The length of the longest sustained note in this event.

        It's possible for different notes to have different sustain values at the same tick.
        """
        return self._longest_sustain(self.sustain)

    @staticmethod
    def _longest_sustain(sustain: ComplexSustain) -> int:
        if isinstance(sustain, int):
            return sustain
        if all(s is None for s in sustain):
            raise ValueError("all sustain values are `None`")
        return max(s for s in sustain if s is not None)

    @functools.cached_property
    def end_tick(self) -> int:
        """The tick immediately after this note ends."""
        return self._end_tick(self.tick, self.longest_sustain)

    @staticmethod
    def _end_tick(tick: int, sustain: int) -> int:
        return tick + sustain

    @classmethod
    def from_parsed_data(
        cls: type[_Self],
        data: NoteEvent.ParsedData | Sequence[NoteEvent.ParsedData],
        prev_event: NoteEvent | None,
        star_power_events: Sequence[StarPowerEvent],
        tatter: TimestampAtTickSupporter,
        proximal_bpm_event_index: int = 0,
        star_power_event_index: int = 0,
    ) -> tuple[_Self, int, int]:
        """Obtain an instance of this object from parsed data.

        This function assumes that, if there are multiple input datas, they all have the same
        ``tick`` value. If they do not, this function's behavior is undefined.

        Args:
            data: The data necessary to create an event. Most likely from a Moonscraper ``.chart``.
            prev_event: The event with the largest tick value less than that of the input data.
            star_power_events: All ``StarPowerEvent``s.
            tatter: An object that can be used to get a timestamp at a particular tick.
            proximal_bpm_event_index: The index of the ``BPMEvent`` with the largest tick value
                smaller than that of this event. For optimization only.
            star_power_event_index: The index of the ``StarPowerEvent`` with the largest tick value
                smaller than that of this event. For optimization only.

        Returns:
            An instance of this object initialized from the input parsed data, along with the index
            of the latest ``BPMEvent`` and ``StarPowerEvent`` not after this event
        """
        datas = data if isinstance(data, Sequence) else [data]

        tick = datas[0].tick
        note = Note.from_parsed_data(data)
        sustain = complex_sustain_from_parsed_data(data)
        is_tap = any(d.note_track_index == NoteTrackIndex.TAP for d in datas)
        is_forced = any(d.note_track_index == NoteTrackIndex.FORCED for d in datas)

        timestamp, proximal_bpm_event_index = tatter.timestamp_at_tick(
            tick, proximal_bpm_event_index=proximal_bpm_event_index
        )

        hopo_state = NoteEvent._compute_hopo_state(
            tatter.resolution,
            tick,
            note,
            is_tap,
            is_forced,
            prev_event,
        )

        star_power_data, star_power_event_index = NoteEvent._compute_star_power_data(
            tick, star_power_events, proximal_star_power_event_index=star_power_event_index
        )

        longest_sustain = cls._longest_sustain(sustain)
        end_tick = cls._end_tick(tick, longest_sustain)
        end_timestamp, _ = tatter.timestamp_at_tick(
            end_tick, proximal_bpm_event_index=proximal_bpm_event_index
        )

        event = cls(
            tick,
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
        star_power_events: Sequence[StarPowerEvent],
        *,
        proximal_star_power_event_index: int = 0,
    ) -> tuple[StarPowerData | None, int]:
        if not star_power_events:
            return None, 0

        if proximal_star_power_event_index >= len(star_power_events):
            raise ValueError(
                "there are no StarPowerEvents at or after index "
                f"{proximal_star_power_event_index} in star_power_events"
            )

        for candidate_index in range(proximal_star_power_event_index, len(star_power_events)):
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

    @dataclasses.dataclass(kw_only=True, frozen=True, repr=False)
    class ParsedData(Event.ParsedData, DictReprMixin):
        _Self = typ.TypeVar("_Self", bound="NoteEvent.ParsedData")

        note_track_index: NoteTrackIndex
        """The note lane active on this chart line."""

        sustain: int
        """The duration in ticks of the active lane in the event represented by this data."""

        # This regex matches a single "N" line within a instrument track section.
        # Match 1: Tick
        # Match 2: Note index
        # Match 3: Sustain (ticks)
        _regex: typ.Final[str] = r"^\s*?(\d+?) = N ([0-7]) (\d+?)\s*?$"
        _regex_prog: typ.Final[typ.Pattern[str]] = re.compile(_regex)

        _unhandled_note_track_index_log_msg_tmpl: typ.Final[
            str
        ] = "unhandled note track index {} at tick {}"

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
            parsed_tick, parsed_note_index, parsed_sustain = (
                int(m.group(1)),
                int(m.group(2)),
                int(m.group(3)),
            )
            note_track_index = NoteTrackIndex(parsed_note_index)
            return cls(
                tick=parsed_tick,
                note_track_index=note_track_index,
                sustain=parsed_sustain,
            )


# TODO: Make this a dataclass.
class SpecialEvent(Event):
    """Provides a regex template for parsing 'S' style chart lines.

    This is typically used only as a base class for more specialized subclasses.
    """

    _Self = typ.TypeVar("_Self", bound="SpecialEvent")

    sustain: typ.Final[int]
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
        """The tick immediately after this event ends."""
        return self.tick + self.sustain

    @classmethod
    def from_parsed_data(
        cls: type[_Self],
        data: SpecialEvent.ParsedData,
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

    @dataclasses.dataclass(kw_only=True, frozen=True, repr=False)
    class ParsedData(Event.ParsedData, DictReprMixin):
        _Self = typ.TypeVar("_Self", bound="SpecialEvent.ParsedData")

        sustain: int
        """The duration in ticks of the event represented by this data."""

        _regex: typ.ClassVar[str]
        _regex_prog: typ.ClassVar[typ.Pattern[str]]

        # Match 1: Tick
        # Match 2: Sustain (ticks)
        _regex_template: typ.Final[str] = r"^\s*?(\d+?) = S {} (\d+?)\s*?$"
        _index_regex: typ.ClassVar[str]

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
            tick, sustain = int(m.group(1)), int(m.group(2))
            return cls(tick=tick, sustain=sustain)


@typ.final
class StarPowerEvent(SpecialEvent):
    """An event representing star power starting at some tick and lasting for some duration."""

    @typ.final
    @dataclasses.dataclass(kw_only=True, frozen=True, repr=False)
    class ParsedData(SpecialEvent.ParsedData, DictReprMixin):
        _index_regex = r"2"
        _regex = SpecialEvent.ParsedData._regex_template.format(_index_regex)
        _regex_prog = re.compile(_regex)


# TODO: Support S 0 ## and S 1 ## (GH1/2 Co-op)


# TODO: Support S 64 ## (Rock Band drum fills)


# TODO: Support E textherewithoutspaces ("track events") within InstrumentTracks.


# TODO: Make this a dataclass (and all events...?).
@typ.final
class TrackEvent(Event):
    """An event representing arbitrary data at a particular tick.

    This is questionably named, as this Python package refers to the various chart file sections
    as "tracks". This event only occurs in instrument tracks.
    """

    _Self = typ.TypeVar("_Self", bound="TrackEvent")

    value: typ.Final[str]
    """The data that this event stores."""

    def __init__(
        self,
        tick: int,
        timestamp: datetime.timedelta,
        value: str,
        proximal_bpm_event_index: int = 0,
    ) -> None:
        super().__init__(tick, timestamp, proximal_bpm_event_index=proximal_bpm_event_index)
        self.value = value

    @classmethod
    def from_parsed_data(
        cls: type[_Self],
        data: TrackEvent.ParsedData,
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
        _Self = typ.TypeVar("_Self", bound="TrackEvent.ParsedData")

        value: str

        # Match 1: Tick
        # Match 2: Event value (to be added by subclass via _value_regex)
        _regex: typ.Final[str] = r"^\s*?(\d+?) = E ([^ ]*?)\s*?$"
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
            tick, value = int(m.group(1)), m.group(2)
            return cls(tick=tick, value=value)
