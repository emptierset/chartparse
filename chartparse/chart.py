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
import itertools
import logging
import re
import typing as typ
from collections.abc import Iterable, Sequence
from datetime import timedelta
from pathlib import Path

from chartparse.exceptions import RegexNotMatchError, UnreachableError
from chartparse.globalevents import GlobalEventsTrack
from chartparse.instrument import Difficulty, Instrument, InstrumentTrack
from chartparse.metadata import Metadata
from chartparse.sync import SyncTrack
from chartparse.tick import Tick
from chartparse.time import Timestamp
from chartparse.util import DictPropertiesEqMixin, DictReprTruncatedSequencesMixin

if typ.TYPE_CHECKING:  # pragma: no cover
    from chartparse.instrument import NoteEvent

logging.basicConfig()
logger = logging.getLogger(__name__)


InstrumentTrackMap = typ.NewType(
    "InstrumentTrackMap", dict[Instrument, dict[Difficulty, InstrumentTrack]]
)


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

    instrument_tracks: typ.Final[InstrumentTrackMap]
    """Contains all of the chart's :class:`~chartparse.instrument.InstrumentTrack` objects."""

    _required_sections: typ.Final[list[str]] = [
        Metadata.section_name,
        SyncTrack.section_name,
        GlobalEventsTrack.section_name,
    ]

    _section_name_regex: typ.Final[str] = r"^\[(.+?)\]$"
    _section_name_regex_prog: typ.Final[typ.Pattern[str]] = re.compile(_section_name_regex)

    _unhandled_section_log_msg_tmpl: typ.Final[str] = "unhandled section titled '{}'"

    def __init__(
        self,
        metadata: Metadata,
        global_events_track: GlobalEventsTrack,
        sync_track: SyncTrack,
        instrument_tracks: InstrumentTrackMap,
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
        section_dict = cls._parse_section_dict(lines)
        if not all(section in section_dict for section in cls._required_sections):
            raise ValueError(
                f"parsed section list {list(section_dict.keys())} does not contain all "
                f"required sections {cls._required_sections}"
            )

        metadata = Metadata.from_chart_lines(section_dict[Metadata.section_name])
        sync_track = SyncTrack.from_chart_lines(
            metadata.resolution, section_dict[SyncTrack.section_name]
        )
        global_events_track = GlobalEventsTrack.from_chart_lines(
            section_dict[GlobalEventsTrack.section_name], sync_track.bpm_events
        )

        instrument_track_name_to_instrument_difficulty_pair: dict[
            str, tuple[Instrument, Difficulty]
        ] = {d.value + i.value: (i, d) for i, d in itertools.product(Instrument, Difficulty)}

        instrument_tracks = InstrumentTrackMap(collections.defaultdict(dict))
        for section_name, section_lines in section_dict.items():
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
                    sync_track.bpm_events,
                )
                instrument_tracks[instrument][difficulty] = track
            elif section_name not in cls._required_sections:
                logger.warning(cls._unhandled_section_log_msg_tmpl.format(section_name))

        return cls(metadata, global_events_track, sync_track, instrument_tracks)

    @classmethod
    def _parse_section_dict(cls, lines: Iterable[str]) -> dict[str, Iterable[str]]:
        d: dict[str, Iterable[str]] = dict()
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
                d[curr_section_name] = itertools.islice(
                    lines, curr_first_line_index, curr_last_line_index + 1
                )
                curr_section_name = None
                curr_first_line_index = None
                curr_last_line_index = None
        return d

    @typ.overload
    def notes_per_second(
        self,
        instrument: Instrument,
        difficulty: Difficulty,
    ) -> float:
        ...  # pragma: no cover

    @typ.overload
    def notes_per_second(
        self,
        instrument: Instrument,
        difficulty: Difficulty,
        start: Timestamp,
    ) -> float:
        ...  # pragma: no cover

    @typ.overload
    def notes_per_second(
        self,
        instrument: Instrument,
        difficulty: Difficulty,
        start: Timestamp,
        end: Timestamp,
    ) -> float:
        ...  # pragma: no cover

    @typ.overload
    def notes_per_second(
        self,
        instrument: Instrument,
        difficulty: Difficulty,
        start: Tick,
    ) -> float:
        ...  # pragma: no cover

    @typ.overload
    def notes_per_second(
        self,
        instrument: Instrument,
        difficulty: Difficulty,
        start: Tick,
        end: Tick,
    ) -> float:
        ...  # pragma: no cover

    def notes_per_second(
        self,
        instrument: Instrument,
        difficulty: Difficulty,
        start: Timestamp | Tick | None = None,
        end: Timestamp | Tick | None = None,
    ) -> float:
        """Returns the average notes per second over the input interval.

        More specifically, this calculates the number of :class:`~chartparse.instrument.NoteEvent`
        objects per second. Chords do not count as multiple "notes" in one instant.

        The interval is closed on both ends.

        Args:
            instrument: The instrument for which the
                :class:`~chartparse.instrument.InstrumentTrack` should be looked up.

            difficulty: The instrument for which the
                :class:`~chartparse.instrument.InstrumentTrack` should be looked up.

            start: The beginning of the interval.
            end: The end of the interval.

        Returns:
            The average notes per second value over the input interval.

        Raises:
            ValueError: If there is no :class:`~chartparse.instrument.InstrumentTrack`
                corresponding to ``instrument`` and ``difficulty``.

            ValueError: If there are no :class:`~chartparse.instrument.NoteEvent` objects on the
                instrument track in question.

            ValueError: If the interval in question is not of positive length.

        """

        try:
            track = self.instrument_tracks[instrument][difficulty]
        except KeyError:
            raise ValueError(
                f"no instrument track for difficulty {difficulty} instrument {instrument}"
            )

        if not track.note_events:
            raise ValueError("notes per second undefined for track with no notes")
        assert track.last_note_end_timestamp is not None

        # Case: Tick or all None
        if start is None or isinstance(start, int):
            assert end is None or isinstance(end, int)
            start_time = (
                self.sync_track.bpm_events.timestamp_at_tick_no_optimize_return(start)
                if start is not None
                else Timestamp(timedelta(0))
            )
            end_time = (
                self.sync_track.bpm_events.timestamp_at_tick_no_optimize_return(end)
                if end is not None
                else track.last_note_end_timestamp
            )
        # Case: Timestamp
        elif isinstance(start, timedelta):
            assert end is None or isinstance(end, timedelta)
            start_time = start if start is not None else Timestamp(timedelta(0))
            end_time = end if end is not None else track.last_note_end_timestamp
        else:  # pragma: no cover
            raise UnreachableError("start must be int, timedelta, or None")

        return self._notes_per_second(track.note_events, start_time, end_time)

    @staticmethod
    def _notes_per_second(
        events: Sequence[NoteEvent],
        start_time: Timestamp,
        end_time: Timestamp,
    ) -> float:
        def is_event_eligible(note: NoteEvent) -> bool:
            return start_time <= note.timestamp <= end_time

        num_events_to_consider = sum(1 for e in events if is_event_eligible(e))
        interval_duration_seconds = (end_time - start_time).total_seconds()
        if interval_duration_seconds <= 0:
            raise ValueError(
                "cannot calculate notes per second for non-positive duration "
                f"interval; got interval of length {interval_duration_seconds} seconds"
            )
        return num_events_to_consider / interval_duration_seconds

    def __str__(self) -> str:
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
