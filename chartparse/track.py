import collections

from chartparse.enums import Note
from chartparse.event import BPMEvent, EventsEvent, NoteEvent, StarPowerEvent, TimeSignatureEvent
from chartparse.exceptions import RegexFatalNotMatchError
from chartparse.util import DictPropertiesEqMixin


class InstrumentTrack(DictPropertiesEqMixin):
    _min_note_instrument_track_index = 0
    _max_note_instrument_track_index = 4
    _open_instrument_track_index = 7
    _forced_instrument_track_index = 5
    _tap_instrument_track_index = 6

    def __init__(self, instrument, difficulty, iterator_getter):
        self.instrument = instrument
        self.difficulty = difficulty
        self.note_events = self._parse_note_events_from_iterable(iterator_getter())
        self.star_power_events = _parse_events_from_iterable(
            iterator_getter(), StarPowerEvent.from_chart_line
        )
        self._populate_star_power_data()

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
            if (
                InstrumentTrack._min_note_instrument_track_index
                <= note_index
                <= InstrumentTrack._max_note_instrument_track_index
            ):
                tick_to_note_array[tick][note_index] = 1
                tick_to_duration_list[tick][note_index] = duration
            elif note_index == InstrumentTrack._open_instrument_track_index:
                # Because `tick_to_note_array` is a defaultdict, simply accessing it at `tick` is
                # sufficient to conjure a bytearray representing an open note.
                tick_to_note_array[tick]
                tick_to_duration_list[tick]
            elif note_index == InstrumentTrack._tap_instrument_track_index:
                tick_to_is_tap[tick] = True
            elif note_index == InstrumentTrack._forced_instrument_track_index:
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

    def _populate_star_power_data(self):
        num_notes = len(self.note_events)

        note_idx_to_star_power_idx = dict()
        note_idx = 0
        for star_power_idx, star_power_event in enumerate(self.star_power_events):
            start_tick = star_power_event.tick
            end_tick = start_tick + star_power_event.duration

            # Seek until the first note after this star power phrase.
            while note_idx < num_notes and self.note_events[note_idx].tick < end_tick:
                note = self.note_events[note_idx]
                if start_tick <= note.tick:
                    note_idx_to_star_power_idx[note_idx] = star_power_idx
                note_idx += 1

        for note_idx, note_event in enumerate(self.note_events):
            current_star_power_idx = note_idx_to_star_power_idx.get(note_idx, None)
            if current_star_power_idx is None:
                continue
            next_star_power_idx = note_idx_to_star_power_idx.get(note_idx + 1, None)
            current_note_is_end_of_phrase = current_star_power_idx != next_star_power_idx
            note_event.star_power_data = NoteEvent.StarPowerData(
                current_star_power_idx, current_note_is_end_of_phrase
            )


class SyncTrack(DictPropertiesEqMixin):
    def __init__(self, iterator_getter):
        self.time_signature_events = _parse_events_from_iterable(
            iterator_getter(), TimeSignatureEvent.from_chart_line
        )
        if self.time_signature_events[0].tick != 0:
            raise ValueError(
                f"first TimeSignatureEvent {self.time_signature_events[0]} must have tick 0"
            )

        self.bpm_events = _parse_events_from_iterable(iterator_getter(), BPMEvent.from_chart_line)
        if self.bpm_events[0].tick != 0:
            raise ValueError(f"first BPMEvent {self.bpm_events[0]} must have tick 0")

    def idx_of_proximal_bpm_event(self, tick, start_idx=0):
        # A BPMEvent is "proximal" relative to tick `T` if it is the
        # BPMEvent with the highest tick value not greater than `T`.
        for idx in range(start_idx, len(self.bpm_events)):
            is_last_bpm_event = idx == len(self.bpm_events) - 1
            next_bpm_event = self.bpm_events[idx + 1] if not is_last_bpm_event else None
            if is_last_bpm_event or next_bpm_event.tick > tick:
                return idx
        raise ValueError(f"there are no BPMEvents at or after index {start_idx} in bpm_events")


class Events(DictPropertiesEqMixin):
    def __init__(self, iterator_getter):
        self.events = _parse_events_from_iterable(iterator_getter(), EventsEvent.from_chart_line)


def _parse_events_from_iterable(iterable, from_chart_line_fn):
    events = []
    for line in iterable:
        try:
            event = from_chart_line_fn(line)
        except RegexFatalNotMatchError:
            continue
        events.append(event)
    events.sort(key=lambda e: e.tick)
    return events
