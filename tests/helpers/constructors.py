import pytest

from chartparse.globalevents import GlobalEvent
from chartparse.instrument import StarPowerEvent, NoteEvent
from chartparse.sync import TimeSignatureEvent, BPMEvent


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


def TimeSignatureEventWithDefaults(
    *,
    tick=pytest.default_tick,
    timestamp=pytest.default_timestamp,
    upper_numeral=pytest.default_upper_time_signature_numeral,
    lower_numeral=pytest.default_lower_time_signature_numeral,
    proximal_bpm_event_idx=None,
):
    return TimeSignatureEvent(
        tick,
        timestamp,
        upper_numeral,
        lower_numeral,
        proximal_bpm_event_idx=proximal_bpm_event_idx,
    )


def BPMEventWithDefaults(
    *,
    tick=pytest.default_tick,
    timestamp=pytest.default_timestamp,
    bpm=pytest.default_bpm,
):
    return BPMEvent(tick, timestamp, bpm)
