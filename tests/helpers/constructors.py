import pytest

from chartparse.globalevents import GlobalEvent
from chartparse.instrument import StarPowerEvent, NoteEvent


def StarPowerEventWithDefaults(
    *,
    tick=pytest.default_tick,
    timestamp=pytest.default_timestamp,
    sustain=pytest.default_sustain,
    proximal_bpm_event_idx=None,
):
    return StarPowerEvent(tick, timestamp, sustain, proximal_bpm_event_idx=proximal_bpm_event_idx)


def NoteEventWithDefaults(
    *,
    tick=pytest.default_tick,
    timestamp=pytest.default_timestamp,
    note=pytest.default_note,
    sustain=pytest.default_sustain,
    is_forced=False,
    is_tap=False,
    star_power_data=None,
):
    return NoteEvent(
        tick,
        timestamp,
        note,
        sustain=sustain,
        is_forced=is_forced,
        is_tap=is_tap,
        star_power_data=star_power_data,
    )


def GlobalEventWithDefaults(
    *,
    tick=pytest.default_tick,
    timestamp=pytest.default_timestamp,
    value=pytest.default_global_event_value,
    proximal_bpm_event_idx=None,
):
    return GlobalEvent(tick, timestamp, value, proximal_bpm_event_idx=proximal_bpm_event_idx)
