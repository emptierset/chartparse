import pytest

from chartparse.instrument import StarPowerEvent, NoteEvent, SpecialEvent, InstrumentTrack


def InstrumentTrackWithDefaults(
    *,
    resolution=pytest.defaults.resolution,
    instrument=pytest.defaults.instrument,
    difficulty=pytest.defaults.difficulty,
    note_events=pytest.defaults.note_events,
    star_power_events=pytest.defaults.star_power_events,
):
    return InstrumentTrack(resolution, instrument, difficulty, note_events, star_power_events)


def SpecialEventWithDefaults(
    *,
    tick=pytest.defaults.tick,
    timestamp=pytest.defaults.timestamp,
    sustain=pytest.defaults.sustain,
    proximal_bpm_event_index=pytest.defaults.proximal_bpm_event_index,
    init_end_tick=False,
):
    s = SpecialEvent(tick, timestamp, sustain, proximal_bpm_event_index=proximal_bpm_event_index)
    if init_end_tick:
        s.end_tick  # accessing this initializes it because it's a cached_property
    return s


def StarPowerEventWithDefaults(
    *,
    tick=pytest.defaults.tick,
    timestamp=pytest.defaults.timestamp,
    sustain=pytest.defaults.sustain,
    proximal_bpm_event_index=pytest.defaults.proximal_bpm_event_index,
    init_end_tick=False,
):
    s = StarPowerEvent(tick, timestamp, sustain, proximal_bpm_event_index=proximal_bpm_event_index)
    if init_end_tick:
        s.end_tick  # accessing this initializes it because it's a cached_property
    return s


def NoteEventWithDefaults(
    *,
    tick=pytest.defaults.tick,
    timestamp=pytest.defaults.timestamp,
    end_timestamp=pytest.defaults.timestamp,
    note=pytest.defaults.note,
    hopo_state=pytest.defaults.hopo_state,
    sustain=pytest.defaults.sustain,
    star_power_data=None,
    proximal_bpm_event_index=pytest.defaults.proximal_bpm_event_index,
):
    return NoteEvent(
        tick,
        timestamp,
        end_timestamp,
        note,
        hopo_state,
        sustain=sustain,
        star_power_data=star_power_data,
        proximal_bpm_event_index=proximal_bpm_event_index,
    )
