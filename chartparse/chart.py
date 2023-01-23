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
import logging
import re
import typing as typ
from collections.abc import Iterable, Sequence
from pathlib import Path

import chartparse.tick
from chartparse.exceptions import ProgrammerError, RegexNotMatchError
from chartparse.globalevents import GlobalEventsTrack
from chartparse.instrument import Difficulty, Instrument, InstrumentTrack
from chartparse.metadata import Metadata
from chartparse.sync import SyncTrack
from chartparse.util import DictPropertiesEqMixin, DictReprTruncatedSequencesMixin

if typ.TYPE_CHECKING:  # pragma: no cover
    from chartparse.instrument import NoteEvent

logging.basicConfig()
logger = logging.getLogger(__name__)


@typ.final
class Chart(DictPropertiesEqMixin, DictReprTruncatedSequencesMixin):
    """A Clone Hero / Moonscraper chart and its relevant gameplay data.

    While it is possible to create this with its initializer, as a user, you will most likely have
    a ``.chart`` file and not the constituent objects necessary to use ``__init__``. To initialize
    a ``Chart`` from a file, you should instead use :meth:`~chartparse.chart.Chart.from_file`.
    """

    metadata: typ.Final[Metadata]
    """The chart's metadata, such as song title or charter name."""

    global_events_track: typ.Final[GlobalEventsTrack]
    """Contains the chart's :class:`~chartparse.globalevents.GlobalEvent` objects"""

    sync_track: typ.Final[SyncTrack]
    """Contains the chart's sync-related events."""

    instrument_tracks: typ.Final[dict[Instrument, dict[Difficulty, InstrumentTrack]]]
    """Contains all of the chart's :class:`~chartparse.instrument.InstrumentTrack` objects."""

    _unhandled_section_log_msg_tmpl: typ.Final[str] = "unhandled section titled '{}'"

    _required_sections: typ.Final[list[str]] = [
        Metadata.section_name,
        SyncTrack.section_name,
        GlobalEventsTrack.section_name,
    ]

    _section_name_regex: typ.Final[str] = r"^\[(.+?)\]$"
    _section_name_regex_prog: typ.Final[typ.Pattern[str]] = re.compile(_section_name_regex)

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

    @classmethod
    def from_filepath(
        cls, path: Path, want_tracks: Sequence[tuple[Instrument, Difficulty]] | None = None
    ) -> Chart:
        """Given a path, parses the contents of its file and returns a new Chart.

        Args:
            path: A ``Path`` object that points to a ``.chart`` file written by Moonscraper. Must
                have at least a ``[Song]``, ``[SyncTrack]``, and ``[Events]`` track.
            want_tracks: An optional sequence of ``Instrument`` & ``Difficulty`` tuples. If
                specified, only the specified instruments and difficulties will be parsed from
                ``path``.

        Returns:
            A ``Chart`` object, initialized with data parsed from ``path``.
        """
        with open(path, "r", encoding="utf-8-sig") as f:
            return Chart.from_file(f, want_tracks=want_tracks)

    @classmethod
    def from_file(
        cls,
        fp: typ.TextIO,
        want_tracks: Sequence[tuple[Instrument, Difficulty]] | None = None,
    ) -> Chart:
        """Given a file object, parses its contents and returns a new Chart.

        Args:
            fp: A file object that allows reading from a .chart file written by Moonscraper. Must
                have at least a ``[Song]``, ``[SyncTrack]``, and ``[Events]`` track.
            want_tracks: An optional sequence of ``Instrument`` & ``Difficulty`` tuples. If
                specified, only the specified instruments and difficulties will be parsed from
                ``fp``.

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
            metadata.resolution, sections[SyncTrack.section_name]
        )
        global_events_track = GlobalEventsTrack.from_chart_lines(
            sections[GlobalEventsTrack.section_name], sync_track
        )

        instrument_track_name_to_instrument_difficulty_pair: dict[
            str, tuple[Instrument, Difficulty]
        ] = {d.value + i.value: (i, d) for i, d in itertools.product(Instrument, Difficulty)}

        instrument_tracks: collections.defaultdict[
            Instrument, dict[Difficulty, InstrumentTrack]
        ] = collections.defaultdict(dict)
        for section_name, section_lines in sections.items():
            if section_name in instrument_track_name_to_instrument_difficulty_pair:
                instrument_difficulty_pair = instrument_track_name_to_instrument_difficulty_pair[
                    section_name
                ]
                if want_tracks is not None and instrument_difficulty_pair not in want_tracks:
                    continue
                instrument, difficulty = instrument_difficulty_pair
                track = InstrumentTrack.from_chart_lines(
                    instrument,
                    difficulty,
                    section_lines,
                    sync_track,
                )
                instrument_tracks[instrument][difficulty] = track
            elif section_name not in cls._required_sections:
                logger.warning(cls._unhandled_section_log_msg_tmpl.format(section_name))

        return cls(metadata, global_events_track, sync_track, instrument_tracks)

    @classmethod
    def _find_sections(cls, lines: Iterable[str]) -> dict[str, Iterable[str]]:
        sections: dict[str, Iterable[str]] = dict()
        curr_section_name = None
        curr_first_line_index = None
        curr_last_line_index = None
        for i, line in enumerate(lines):
            if curr_section_name is None:
                m = cls._section_name_regex_prog.match(line)
                if not m:
                    raise RegexNotMatchError(cls._section_name_regex, line)
                curr_section_name = m.group(1)
            elif line == "{":
                curr_first_line_index = i + 1
            elif line == "}":
                curr_last_line_index = i - 1
                sections[curr_section_name] = itertools.islice(
                    lines, curr_first_line_index, curr_last_line_index + 1
                )
                curr_section_name = None
                curr_first_line_index = None
                curr_last_line_index = None
        return sections

    def _seconds_from_ticks_at_bpm(self, ticks: int, bpm: float) -> float:
        return chartparse.tick.seconds_from_ticks_at_bpm(ticks, bpm, self.metadata.resolution)

    def notes_per_second(
        self,
        instrument: Instrument,
        difficulty: Difficulty,
        start_time: datetime.timedelta | None = None,
        end_time: datetime.timedelta | None = None,
        start_tick: int | None = None,
        end_tick: int | None = None,
        start_seconds: float | None = None,
        end_seconds: float | None = None,
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

        if not track.note_events:
            raise ValueError("notes per second undefined for track with no notes")

        all_start_args_none = num_of_start_args_none == len(start_args)
        if (start_tick is not None) or all_start_args_none:
            interval_start_time = (
                self.sync_track.timestamp_at_tick(start_tick, self.metadata.resolution)[0]
                if start_tick is not None
                else datetime.timedelta(0)
            )
            interval_end_time = (
                self.sync_track.timestamp_at_tick(end_tick, self.metadata.resolution)[0]
                if end_tick is not None
                # ValueError is raised above if there are no NoteEvents, which is the only case
                # where track.last_note_end_timestamp is None.
                else typ.cast(datetime.timedelta, track.last_note_end_timestamp)
            )
        elif start_time is not None:
            interval_start_time = start_time if start_time is not None else datetime.timedelta(0)
            # ValueError is raised above if there are no NoteEvents, which is the only case where
            # track.last_note_end_timestamp is None.
            interval_end_time = (
                end_time
                if end_time is not None
                else typ.cast(datetime.timedelta, track.last_note_end_timestamp)
            )
        elif start_seconds is not None:
            interval_start_time = (
                datetime.timedelta(seconds=start_seconds)
                if start_seconds is not None
                else datetime.timedelta(0)
            )
            interval_end_time = (
                datetime.timedelta(seconds=end_seconds)
                if end_seconds is not None
                # ValueError is raised above if there are no NoteEvents, which is the only case
                # where track.last_note_end_timestamp is None.
                else typ.cast(datetime.timedelta, track.last_note_end_timestamp)
            )
        else:  # pragma: no cover
            raise ProgrammerError

        return self._notes_per_second(track.note_events, interval_start_time, interval_end_time)

    @staticmethod
    def _notes_per_second(
        events: Sequence[NoteEvent],
        interval_start_time: datetime.timedelta,
        interval_end_time: datetime.timedelta,
    ) -> float:
        def is_event_eligible(note: NoteEvent) -> bool:
            return interval_start_time <= note.timestamp <= interval_end_time

        num_events_to_consider = sum(1 for e in events if is_event_eligible(e))
        interval_duration_seconds = (interval_end_time - interval_start_time).total_seconds()
        return num_events_to_consider / interval_duration_seconds

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

    def __getitem__(self, instrument: Instrument) -> dict[Difficulty, InstrumentTrack]:
        return self.instrument_tracks[instrument]
