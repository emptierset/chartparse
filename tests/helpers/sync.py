import pytest

from chartparse.sync import TimeSignatureEvent, BPMEvent


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
