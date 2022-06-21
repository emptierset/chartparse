import collections
import datetime
import itertools
import re

from chartparse.enums import Difficulty, Instrument
from chartparse.exceptions import RegexFatalNotMatchError
from chartparse.globalevents import GlobalEventsTrack
from chartparse.instrument import InstrumentTrack
from chartparse.metadata import Metadata
from chartparse.sync import SyncTrack
from chartparse.util import DictPropertiesEqMixin, iterate_from_second_elem

_max_timedelta = datetime.datetime.max - datetime.datetime.min


class Chart(DictPropertiesEqMixin):
    _required_metadata = ("resolution",)

    def __init__(self, metadata, global_events_track, sync_track, instrument_tracks):
        if not all(hasattr(metadata, p) for p in self._required_metadata):
            raise ValueError(
                f"metadata list {list(metadata.__dict__.keys())} does not "
                f"contain all required metadata {self._required_metadata}"
            )

        self.metadata = metadata
        self.global_events_track = global_events_track
        self.sync_track = sync_track
        self.instrument_tracks = instrument_tracks

        self._populate_bpm_event_timestamps()
        self._populate_event_timestamps(self.sync_track.time_signature_events)
        self._populate_event_timestamps(self.global_events_track.text_events)
        self._populate_event_timestamps(self.global_events_track.section_events)
        self._populate_event_timestamps(self.global_events_track.lyric_events)
        for instrument, difficulties in self.instrument_tracks.items():
            for difficulty, track in difficulties.items():
                self._populate_event_timestamps(track.note_events)
                self._populate_event_timestamps(track.star_power_events)

    _required_sections = ("Song", "SyncTrack")
    _instrument_track_name_to_instrument_difficulty_pair = {
        d + i: (Instrument(i), Difficulty(d))
        for i, d in itertools.product(Instrument.all_values(), Difficulty.all_values())
    }

    @classmethod
    def from_file(cls, fp):
        lines = fp.read().splitlines()
        sections = cls._find_sections(lines)
        if not all(section in sections for section in cls._required_sections):
            raise ValueError(
                f"parsed section list {list(sections.keys())} does not contain all "
                f"required sections {cls._required_sections}"
            )

        instrument_tracks = collections.defaultdict(dict)
        for section_name, iterator_getter in sections.items():
            # TODO: Don't hardcode the section names.
            if section_name == "Song":
                metadata = Metadata.from_chart_lines(iterator_getter())
            elif section_name == "Events":
                global_events_track = GlobalEventsTrack.from_chart_lines(iterator_getter)
            elif section_name == "SyncTrack":
                sync_track = SyncTrack.from_chart_lines(iterator_getter)
            elif section_name in cls._instrument_track_name_to_instrument_difficulty_pair:
                instrument, difficulty = cls._instrument_track_name_to_instrument_difficulty_pair[
                    section_name
                ]
                track = InstrumentTrack.from_chart_lines(instrument, difficulty, iterator_getter)
                instrument_tracks[instrument][difficulty] = track
            else:
                pass
                # TODO: Log unhandled section.

        return cls(metadata, global_events_track, sync_track, instrument_tracks)

    _section_name_regex = r"^\[(.+?)\]$"
    _section_name_regex_prog = re.compile(_section_name_regex)

    @classmethod
    def _find_sections(cls, lines):
        sections = dict()
        curr_section_name = None
        curr_first_line_idx = None
        curr_last_line_idx = None
        for i, line in enumerate(lines):
            if curr_section_name is None:
                m = cls._section_name_regex_prog.match(line)
                if not m:
                    raise RegexFatalNotMatchError(cls._section_name_regex, line)
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

    def _populate_bpm_event_timestamps(self):
        self.sync_track.bpm_events[0].timestamp = datetime.timedelta(0)
        for i, cur_event in enumerate(
            iterate_from_second_elem(self.sync_track.bpm_events), start=1
        ):
            prev_event = self.sync_track.bpm_events[i - 1]
            ticks_since_prev = cur_event.tick - prev_event.tick
            seconds_since_prev = self._seconds_from_ticks_at_bpm(ticks_since_prev, prev_event.bpm)
            cur_event.timestamp = prev_event.timestamp + datetime.timedelta(
                seconds=seconds_since_prev
            )

    def _populate_event_timestamps(self, events):
        proximal_bpm_event_idx = 0
        for i, event in enumerate(events):
            timestamp, proximal_bpm_event_idx = self._timestamp_at_tick(
                event.tick,
                start_bpm_event_index=proximal_bpm_event_idx,
            )
            event.timestamp = timestamp

    def _timestamp_at_tick(self, tick, start_bpm_event_index=0):
        proximal_bpm_event_idx = self.sync_track.idx_of_proximal_bpm_event(
            tick, start_idx=start_bpm_event_index
        )
        proximal_bpm_event = self.sync_track.bpm_events[proximal_bpm_event_idx]
        ticks_since_proximal_bpm_event = tick - proximal_bpm_event.tick
        seconds_since_proximal_bpm_event = self._seconds_from_ticks_at_bpm(
            ticks_since_proximal_bpm_event, proximal_bpm_event.bpm
        )
        timedelta_since_proximal_bpm_event = datetime.timedelta(
            seconds=seconds_since_proximal_bpm_event
        )
        timestamp = proximal_bpm_event.timestamp + timedelta_since_proximal_bpm_event
        return timestamp, proximal_bpm_event_idx

    def _seconds_from_ticks_at_bpm(self, ticks, bpm):
        if bpm <= 0:
            raise ValueError(f"bpm {bpm} must be positive")
        ticks_per_minute = bpm * self.metadata.resolution
        ticks_per_second = ticks_per_minute / 60
        seconds_per_tick = 1 / ticks_per_second
        return ticks * seconds_per_tick

    def notes_per_second(
        self,
        instrument,
        difficulty,
        start_time=None,
        end_time=None,
        start_tick=None,
        end_tick=None,
        start_seconds=None,
        end_seconds=None,
    ):
        start_args = (start_time, start_seconds, start_tick)
        num_of_start_args_none = start_args.count(None)
        if num_of_start_args_none < 2:
            raise ValueError(
                f"no more than one of start_time {start_time}, start_seconds {start_seconds}, "
                f"and start_tick {start_tick} can be non-None"
            )
        all_start_args_none = num_of_start_args_none == len(start_args)

        def event_is_eligible_by_tick(note):
            lower_bound = start_tick if start_tick is not None else 0
            upper_bound = end_tick if end_tick is not None else float("inf")
            return lower_bound <= note.tick <= upper_bound

        def event_is_eligible_by_time(note):
            lower_bound = start_time if start_time is not None else datetime.timedelta(0)
            upper_bound = end_time if end_time is not None else _max_timedelta
            return lower_bound <= note.timestamp <= upper_bound

        def event_is_eligible_by_seconds(note):
            lower_bound = (
                datetime.timedelta(seconds=start_seconds)
                if start_seconds is not None
                else datetime.timedelta(0)
            )
            upper_bound = (
                datetime.timedelta(seconds=end_seconds)
                if end_seconds is not None
                else _max_timedelta
            )
            return lower_bound <= note.timestamp <= upper_bound

        if (start_tick is not None) or all_start_args_none:
            event_is_eligible_fn = event_is_eligible_by_tick
        elif start_time is not None:
            event_is_eligible_fn = event_is_eligible_by_time
        elif start_seconds is not None:
            event_is_eligible_fn = event_is_eligible_by_seconds
        else:
            raise RuntimeError(
                "unhandled input combination; should be impossible"
            )  # pragma: no cover

        try:
            track = self.instrument_tracks[instrument][difficulty]
        except KeyError:
            raise ValueError(
                f"no instrument track for difficulty {difficulty} instrument {instrument}"
            )
        note_events_to_consider = list(filter(event_is_eligible_fn, track.note_events))
        if len(note_events_to_consider) < 2:
            raise ValueError(
                "cannot determine average notes per second value of phrase with fewer than 2 "
                f"NoteEvents: {note_events_to_consider}"
            )

        return self._notes_per_second_from_note_events(note_events_to_consider)

    @staticmethod
    def _notes_per_second_from_note_events(events):
        first_event = events[0]
        last_event = events[-1]
        phrase_duration_seconds = (last_event.timestamp - first_event.timestamp).total_seconds()
        return len(events) / phrase_duration_seconds
