import pytest

from chartparse.sync import TimeSignatureEvent, BPMEvent, SyncTrack


def SyncTrackWithDefaults(
    *,
    resolution=pytest.defaults.resolution,
    time_signature_events=pytest.defaults.time_signature_events,
    bpm_events=pytest.defaults.bpm_events,
):
    return SyncTrack(resolution, time_signature_events, bpm_events)


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
