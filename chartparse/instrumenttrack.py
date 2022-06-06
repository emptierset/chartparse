import collections

import chartparse.track
from chartparse.enums import Note
from chartparse.event import NoteEvent, StarPowerEvent
from chartparse.util import DictPropertiesEqMixin

_min_note_instrument_track_index = 0
_max_note_instrument_track_index = 4
_open_instrument_track_index = 7
_forced_instrument_track_index = 5
_tap_instrument_track_index = 6


class InstrumentTrack(DictPropertiesEqMixin):
    def __init__(self, instrument, difficulty, iterator_getter):
        self.instrument = instrument
        self.difficulty = difficulty
        self.note_events = self._parse_note_events_from_iterable(iterator_getter())
        self.star_power_events = chartparse.track.parse_events_from_iterable(
            iterator_getter(), StarPowerEvent.from_chart_line
        )

    def __str__(self):  # pragma: no cover
        return (
            f"Instrument: {self.instrument}\n"
            f"Difficulty: {self.difficulty}\n"
            f"Note count: {len(self.note_events)}\n"
            f"Star power phrase count: {len(self.star_power_events)}"
        )

    @staticmethod
    def _parse_note_events_from_iterable(iterable):
        tick_to_note_array = collections.defaultdict(lambda: bytearray(5))
        tick_to_duration_list = collections.defaultdict(lambda: [None] * 5)
        tick_to_is_tap = collections.defaultdict(bool)
        tick_to_is_forced = collections.defaultdict(bool)
        for line in iterable:
            m = NoteEvent._regex_prog.match(line)
            if not m:
                continue
            tick, note_index, duration = int(m.group(1)), int(m.group(2)), int(m.group(3))
            if _min_note_instrument_track_index <= note_index <= _max_note_instrument_track_index:
                tick_to_note_array[tick][note_index] = 1
                tick_to_duration_list[tick][note_index] = duration
            elif note_index == _tap_instrument_track_index:
                tick_to_is_tap[tick] = True
            elif note_index == _forced_instrument_track_index:
                tick_to_is_forced[tick] = True
            else:  # pragma: no cover
                # TODO: Log unhandled instrument track note index.
                pass

        events = []
        for tick in tick_to_note_array.keys():
            note = Note(tick_to_note_array[tick])
            event = NoteEvent(
                tick,
                note,
                duration=tick_to_duration_list[tick],
                is_forced=tick_to_is_forced[tick],
                is_tap=tick_to_is_tap[tick],
            )
            events.append(event)
        events.sort(key=lambda e: e.tick)

        return events
