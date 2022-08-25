import pytest

from chartparse.instrument import StarPowerEvent, NoteEvent, SpecialEvent


def SpecialEventWithDefaults(
    *,
    tick=pytest.defaults.tick,
    timestamp=pytest.defaults.timestamp,
    sustain=pytest.defaults.sustain,
    proximal_bpm_event_idx=0,
    init_end_tick=False,
):
    s = SpecialEvent(tick, timestamp, sustain, proximal_bpm_event_idx=proximal_bpm_event_idx)
    if init_end_tick:
        s.end_tick  # accessing this initializes it because it's a cached_property
    return s


def StarPowerEventWithDefaults(
    *,
    tick=pytest.defaults.tick,
    timestamp=pytest.defaults.timestamp,
    sustain=pytest.defaults.sustain,
    proximal_bpm_event_idx=0,
    init_end_tick=False,
):
    s = StarPowerEvent(tick, timestamp, sustain, proximal_bpm_event_idx=proximal_bpm_event_idx)
    if init_end_tick:
        s.end_tick  # accessing this initializes it because it's a cached_property
    return s


def NoteEventWithDefaults(
    *,
    tick=pytest.defaults.tick,
    timestamp=pytest.defaults.timestamp,
    note=pytest.defaults.note,
    hopo_state=pytest.defaults.hopo_state,
    sustain=pytest.defaults.sustain,
    star_power_data=None,
):
    return NoteEvent(
        tick,
        timestamp,
        note,
        hopo_state,
        sustain=sustain,
        star_power_data=star_power_data,
    )
