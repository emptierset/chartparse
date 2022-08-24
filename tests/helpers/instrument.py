import pytest

from chartparse.instrument import StarPowerEvent, NoteEvent


def StarPowerEventWithDefaults(
    *,
    tick=pytest.defaults.tick,
    timestamp=pytest.defaults.timestamp,
    sustain=pytest.defaults.sustain,
    proximal_bpm_event_idx=0,
):
    return StarPowerEvent(tick, timestamp, sustain, proximal_bpm_event_idx=proximal_bpm_event_idx)


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
