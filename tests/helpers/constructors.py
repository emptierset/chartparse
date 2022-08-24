import pytest

from chartparse.datastructures import ImmutableSortedList
from chartparse.globalevents import GlobalEvent
from chartparse.instrument import StarPowerEvent, NoteEvent
from chartparse.sync import TimeSignatureEvent, BPMEvent


def AlreadySortedImmutableSortedList(xs):
    return ImmutableSortedList(xs, already_sorted=True)


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
    sustain=pytest.defaults.sustain,
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
    tick=pytest.defaults.tick,
    timestamp=pytest.defaults.timestamp,
    value=pytest.defaults.global_event_value,
    proximal_bpm_event_idx=None,
):
    return GlobalEvent(tick, timestamp, value, proximal_bpm_event_idx=proximal_bpm_event_idx)


def TimeSignatureEventWithDefaults(
    *,
    tick=pytest.defaults.tick,
    timestamp=pytest.defaults.timestamp,
    upper_numeral=pytest.defaults.upper_time_signature_numeral,
    lower_numeral=pytest.defaults.lower_time_signature_numeral,
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
    tick=pytest.defaults.tick,
    timestamp=pytest.defaults.timestamp,
    bpm=pytest.defaults.bpm,
):
    return BPMEvent(tick, timestamp, bpm)
