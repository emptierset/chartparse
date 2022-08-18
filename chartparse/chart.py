"""For representing the data of a ``.chart`` file as a object.

This module is the main entrypoint to this package. Typically, a
developer needs only to create a ``Chart`` object and then inspect
its attributes:

Example:
    Creating a ``Chart`` object::

        from chartparse.chart import Chart

        chart = Chart.from_file("path/to/file.chart")

.. _Google Python Style Guide:
    http://google.github.io/styleguide/pyguide.html

"""

from __future__ import annotations

import collections
import datetime
import itertools
import re
import typing
from collections.abc import Callable, Iterable, Iterator, Sequence
from pathlib import Path
from typing import Final, Optional, TextIO

import chartparse.tick
from chartparse.exceptions import RegexNotMatchError
from chartparse.globalevents import GlobalEventsTrack
from chartparse.hints import T
from chartparse.instrument import Difficulty, Instrument, InstrumentTrack, NoteEvent
from chartparse.metadata import Metadata
from chartparse.sync import SyncTrack
from chartparse.util import DictPropertiesEqMixin, DictReprTruncatedSequencesMixin

_max_timedelta = datetime.datetime.max - datetime.datetime.min


@typing.final
class Chart(DictPropertiesEqMixin, DictReprTruncatedSequencesMixin):
    """A Clone Hero / Moonscraper chart and its relevant gameplay data.

    While it is possible to create this with its initializer, as a user, you will most likely have
    a ``.chart`` file and not the constituent objects necessary to use ``__init__``. To initialize
    a ``Chart`` from a file, you should instead use :meth:`~chartparse.chart.Chart.from_file`.
    """

    metadata: Final[Metadata]
    """The chart's metadata, such as song title or charter name."""

    global_events_track: Final[GlobalEventsTrack]
    """Contains the chart's :class:`~chartparse.globalevents.GlobalEvent` objects"""

    sync_track: Final[SyncTrack]
    """Contains the chart's sync-related events."""

    instrument_tracks: Final[dict[Instrument, dict[Difficulty, InstrumentTrack]]]
    """Contains all of the chart's :class:`~chartparse.instrument.InstrumentTrack` objects."""

    def __init__(
        self,
        metadata: Metadata,
        global_events_track: GlobalEventsTrack,
        sync_track: SyncTrack,
        instrument_tracks: dict[Instrument, dict[Difficulty, InstrumentTrack]],
    ) -> None:
        """Instantiates all instance attributes and populates timestamps & note HOPO states."""

        self.metadata = metadata
        self.global_events_track = global_events_track
        self.sync_track = sync_track
        self.instrument_tracks = instrument_tracks

        for instrument, difficulties in self.instrument_tracks.items():
            for difficulty, track in difficulties.items():
                self._populate_note_event_hopo_states(track.note_events)
                self._populate_last_note_timestamp(track)

    @classmethod
    def from_filepath(cls, path: Path) -> Chart:
        """Given a path, parses the contents of its file and returns a new Chart.

        Args:
            path: A ``Path`` object that points to a ``.chart`` file written by Moonscraper. Must
                have a ``[Song]`` section and a ``[SyncTrack]`` section.

        Returns:
            A ``Chart`` object, initialized with data parsed from ``path``.
        """
        with open(path, "r", encoding="utf-8-sig") as f:
            return Chart.from_file(f)

    _required_sections: Final[list[str]] = [Metadata.section_name, SyncTrack.section_name]

    # TODO: Validate that all events are in strictly increasing or non-decreasing (depending on the
    # track) tick order.
    @classmethod
    def from_file(cls, fp: TextIO) -> Chart:
        """Given a file object, parses its contents and returns a new Chart.

        Args:
            fp: A file object that allows reading from a .chart file written by Moonscraper.  Must
                have a ``[Song]`` section and a ``[SyncTrack]`` section.

        Returns:
            A ``Chart`` object, initialized with data parsed from ``fp``.
        """
        lines = fp.read().splitlines()
        sections = cls._find_sections(lines)
        if not all(section in sections for section in cls._required_sections):
            raise ValueError(
                f"parsed section list {list(sections.keys())} does not contain all "
                f"required sections {cls._required_sections}"
            )

        metadata = Metadata.from_chart_lines(sections[Metadata.section_name])
        sync_track = SyncTrack.from_chart_lines(
            sections[SyncTrack.section_name], metadata.resolution
        )

        instrument_track_name_to_instrument_difficulty_pair: dict[
            str, tuple[Instrument, Difficulty]
        ] = {
            d + i: (Instrument(i), Difficulty(d))
            for i, d in typing.cast(
                Iterable[tuple[str, str]],
                itertools.product(Instrument.all_values(), Difficulty.all_values()),
            )
        }

        instrument_tracks: collections.defaultdict[
            Instrument, dict[Difficulty, InstrumentTrack]
        ] = collections.defaultdict(dict)
        for section_name, iterator_getter in sections.items():
            if section_name == GlobalEventsTrack.section_name:
                global_events_track = GlobalEventsTrack.from_chart_lines(
                    iterator_getter, sync_track.timestamp_at_tick, metadata.resolution
                )
            elif section_name in instrument_track_name_to_instrument_difficulty_pair:
                instrument, difficulty = instrument_track_name_to_instrument_difficulty_pair[
                    section_name
                ]
                track = InstrumentTrack.from_chart_lines(
                    instrument,
                    difficulty,
                    iterator_getter,
                    sync_track.timestamp_at_tick,
                    metadata.resolution,
                )
                instrument_tracks[instrument][difficulty] = track
            # TODO: [Logging] Log unhandled sections that also aren't in cls._required_sections.

        return cls(metadata, global_events_track, sync_track, instrument_tracks)

    _section_name_regex = r"^\[(.+?)\]$"
    _section_name_regex_prog = re.compile(_section_name_regex)

    @classmethod
    def _find_sections(cls, lines: Iterable[str]) -> dict[str, Callable[[], Iterable[str]]]:
        sections: dict[str, Callable[[], Iterable[str]]] = dict()
        curr_section_name = None
        curr_first_line_idx = None
        curr_last_line_idx = None
        for i, line in enumerate(lines):
            if curr_section_name is None:
                m = cls._section_name_regex_prog.match(line)
                if not m:
                    raise RegexNotMatchError(cls._section_name_regex, line)
                curr_section_name = m.group(1)
            elif line == "{":
                curr_first_line_idx = i + 1
            elif line == "}":
                curr_last_line_idx = i - 1
                # Set default values for x and y so their current values are
                # captured, rather than references to these local variables.
                iterator_getter = (
                    lambda x=curr_first_line_idx, y=curr_last_line_idx: itertools.islice(
                        lines, x, y + 1
                    )
                )
                sections[curr_section_name] = iterator_getter
                curr_section_name = None
                curr_first_line_idx = None
                curr_last_line_idx = None
        return sections

    def _populate_last_note_timestamp(self, track: InstrumentTrack) -> None:
        if len(track.note_events) == 0:
            return
        last_event = track.note_events[-1]
        last_tick = last_event.tick + last_event.longest_sustain
        track._last_note_timestamp, _ = self.sync_track.timestamp_at_tick(
            last_tick, self.metadata.resolution
        )

    def _populate_note_event_hopo_states(self, events: Sequence[NoteEvent]) -> None:
        if not events:
            return

        for i, cur_event in enumerate(events):
            previous_event = events[i - 1] if i > 0 else None
            cur_event._populate_hopo_state(self.metadata.resolution, previous_event)

    def _seconds_from_ticks_at_bpm(self, ticks: int, bpm: float) -> float:
        return chartparse.tick.seconds_from_ticks_at_bpm(ticks, bpm, self.metadata.resolution)

    def notes_per_second(
        self,
        instrument: Instrument,
        difficulty: Difficulty,
        start_time: Optional[datetime.timedelta] = None,
        end_time: Optional[datetime.timedelta] = None,
        start_tick: Optional[int] = None,
        end_tick: Optional[int] = None,
        start_seconds: Optional[float] = None,
        end_seconds: Optional[float] = None,
    ) -> float:
        """Returns the average notes per second over the input interval.

        More specifically, this calculates the number of :class:`~chartparse.instrument.NoteEvent`
        objects per second. Chords do not count as multiple "notes" in one instant.

        The interval is always a closed interval.

        You may pass one or zero of ``start_time``, ``start_tick``, and ``start_seconds``, or else
        ``ValueError`` will be raised.  If none of ``start_time``, ``start_tick``, and
        ``start_seconds`` are passed, the beginning of the track will be treated as the start of
        the interval.  If none of ``end_time``, ``end_tick``, and ``end_seconds`` are passed, the
        end of the track will be treated as the end of the interval.

        Args:
            instrument: The instrument for which the
                :class:`~chartparse.instrument.InstrumentTrack` should be looked up.
            difficulty: The instrument for which the
                :class:`~chartparse.instrument.InstrumentTrack` should be looked up.
            start_time: The beginning of the interval.
            end_time: The end of the interval.
            start_tick: The beginning of the interval.
            end_tick: The end of the interval.
            start_seconds: The beginning of the interval.
            end_seconds: The end of the interval.

        Returns:
            The average notes per second value over the input interval.

        Raises:
            ValueError: If more than one of ``start_time``, ``start_tick``, and ``start_seconds``
                is ``None``.
            ValueError: If there is no :class:`~chartparse.instrument.InstrumentTrack`
                corresponding to ``instrument`` and ``difficulty``.
            ValueError: If there are fewer than two :class:`~chartparse.instrument.NoteEvent`
                objects within the indicated interval.
        """

        start_args = (start_time, start_seconds, start_tick)
        num_of_start_args_none = start_args.count(None)
        if num_of_start_args_none < 2:
            raise ValueError(
                f"no more than one of start_time {start_time}, start_seconds {start_seconds}, "
                f"and start_tick {start_tick} can be non-None"
            )

        try:
            track = self.instrument_tracks[instrument][difficulty]
        except KeyError:
            raise ValueError(
                f"no instrument track for difficulty {difficulty} instrument {instrument}"
            )

        all_start_args_none = num_of_start_args_none == len(start_args)
        if (start_tick is not None) or all_start_args_none:
            lower_bound = (
                self.sync_track.timestamp_at_tick(start_tick, self.metadata.resolution)[0]
                if start_tick is not None
                else datetime.timedelta(0)
            )
            upper_bound = (
                self.sync_track.timestamp_at_tick(end_tick, self.metadata.resolution)[0]
                if end_tick is not None
                else track._last_note_timestamp
            )
        elif start_time is not None:
            lower_bound = start_time if start_time is not None else datetime.timedelta(0)
            upper_bound = end_time if end_time is not None else track._last_note_timestamp
        elif start_seconds is not None:
            lower_bound = (
                datetime.timedelta(seconds=start_seconds)
                if start_seconds is not None
                else datetime.timedelta(0)
            )
            upper_bound = (
                datetime.timedelta(seconds=end_seconds)
                if end_seconds is not None
                else track._last_note_timestamp
            )
        else:
            raise RuntimeError(
                "unhandled input combination; should be impossible"
            )  # pragma: no cover

        return self._notes_per_second(track.note_events, lower_bound, upper_bound)

    @staticmethod
    def _notes_per_second(
        events: Sequence[NoteEvent],
        lower_bound: datetime.timedelta,
        upper_bound: datetime.timedelta,
    ) -> float:
        def is_event_eligible(note: NoteEvent) -> bool:
            assert note.timestamp is not None
            return lower_bound <= note.timestamp <= upper_bound

        num_events_to_consider = sum(1 for e in events if is_event_eligible(e))
        phrase_duration_seconds = (upper_bound - lower_bound).total_seconds()
        return num_events_to_consider / phrase_duration_seconds

    def __str__(self) -> str:  # pragma: no cover
        items = []
        if hasattr(self, "metadata"):
            items.append(f"{self.metadata}")
        if hasattr(self, "global_events_track"):
            items.append(f"{self.global_events_track}")
        if hasattr(self, "sync_track"):
            items.append(f"{self.sync_track}")
        if hasattr(self, "instrument_tracks"):
            for _, difficulty_dict in self.instrument_tracks.items():
                for _, track in difficulty_dict.items():
                    items.append(f"{track}")

        item_string = ",\n  ".join(items)
        return f"{type(self).__name__}(\n  {item_string})"


def _iterate_from_second_elem(xs: Sequence[T]) -> Iterator[T]:
    """Given an iterable ``xs``, return an iterator that skips ``xs[0]``.

    Args:
        xs: Any non-exhausted iterable.

    Returns:
        A iterator that iterates over ``xs``, ignoring the first element.
    """
    it = iter(xs)
    next(it)
    yield from it
