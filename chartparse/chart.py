import collections
import datetime
import itertools
import re

from chartparse.enums import Difficulty, Instrument
from chartparse.eventstrack import Events
from chartparse.instrumenttrack import InstrumentTrack
from chartparse.properties import Properties
from chartparse.synctrack import SyncTrack
from chartparse.util import iterate_from_second_elem


class Chart(object):
    _required_sections = ("Song", "SyncTrack")
    _instrument_track_name_to_instrument_difficulty_pair = {
        d + i: (Instrument(i), Difficulty(d))
        for i, d in itertools.product(Instrument.all_values(), Difficulty.all_values())
    }

    def __init__(self, fp):
        lines = fp.read().splitlines()
        sections = self._find_sections(lines)
        if not all(section in sections for section in self._required_sections):
            raise ValueError(
                f"parsed section list {list(sections.keys())} does not contain all "
                f"required sections {self._required_sections}"
            )

        self.instrument_tracks = collections.defaultdict(dict)
        for section_name, iterator_getter in sections.items():
            if section_name == "Song":
                self.properties = Properties.from_chart_lines(iterator_getter())
            elif section_name == "Events":
                self.events_track = Events(iterator_getter)
            elif section_name == "SyncTrack":
                self.sync_track = SyncTrack(iterator_getter)
            elif section_name in self._instrument_track_name_to_instrument_difficulty_pair:
                instrument, difficulty = self._instrument_track_name_to_instrument_difficulty_pair[
                    section_name
                ]
                track = InstrumentTrack(instrument, difficulty, iterator_getter)
                self.instrument_tracks[instrument][difficulty] = track
            else:
                # TODO: Log unhandled section.
                pass

        self._populate_bpm_event_timestamps()
        self._populate_event_timestamps(self.sync_track.time_signature_events)
        self._populate_event_timestamps(self.events_track.events)
        for instrument, difficulties in self.instrument_tracks.items():
            for difficulty, track in difficulties.items():
                self._populate_event_timestamps(track.note_events)
                self._populate_event_timestamps(track.star_power_events)

    _section_name_regex_prog = re.compile(r"^\[(.+?)\]$")

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
                    raise ValueError(f"could not parse section name from line '{line}'")
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
            seconds_since_prev = self._seconds_from_ticks(ticks_since_prev, prev_event.bpm)
            cur_event.timestamp = prev_event.timestamp + datetime.timedelta(
                seconds=seconds_since_prev
            )

    def _populate_event_timestamps(self, events):
        # A BPMEvent is "proximal" relative to another event `E` if it is the
        # BPMEvent with the highest tick value not greater than that of `E`.
        def idx_of_proximal_bpm_event(event, start_idx=0):
            for idx in range(start_idx, len(self.sync_track.bpm_events)):
                is_last_bpm_event = idx == len(self.sync_track.bpm_events) - 1
                next_bpm_event = (
                    self.sync_track.bpm_events[idx + 1] if not is_last_bpm_event else None
                )
                if is_last_bpm_event or next_bpm_event.tick > event.tick:
                    return idx

        proximal_bpm_event_idx = 0
        for i, event in enumerate(events):
            proximal_bpm_event_idx = idx_of_proximal_bpm_event(
                event, start_idx=proximal_bpm_event_idx
            )
            proximal_bpm_event = self.sync_track.bpm_events[proximal_bpm_event_idx]
            ticks_since_proximal_bpm_event = event.tick - proximal_bpm_event.tick
            seconds_since_proximal_bpm_event = self._seconds_from_ticks(
                ticks_since_proximal_bpm_event, proximal_bpm_event.bpm
            )
            timedelta_since_proximal_bpm_event = datetime.timedelta(
                seconds=seconds_since_proximal_bpm_event
            )
            event.timestamp = proximal_bpm_event.timestamp + timedelta_since_proximal_bpm_event

    def _seconds_from_ticks(self, ticks, bpm):
        if bpm <= 0:
            raise ValueError(f"bpm {bpm} must be positive")
        ticks_per_minute = bpm * self.properties.resolution
        ticks_per_second = ticks_per_minute / 60
        seconds_per_tick = 1 / ticks_per_second
        return ticks * seconds_per_tick
