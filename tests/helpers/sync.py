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
    proximal_bpm_event_index=pytest.defaults.proximal_bpm_event_index,
):
    return TimeSignatureEvent(
        tick,
        timestamp,
        upper_numeral,
        lower_numeral,
        proximal_bpm_event_index=proximal_bpm_event_index,
    )


def BPMEventWithDefaults(
    *,
    tick=pytest.defaults.tick,
    timestamp=pytest.defaults.timestamp,
    bpm=pytest.defaults.bpm,
    proximal_bpm_event_index=pytest.defaults.proximal_bpm_event_index,
):
    return BPMEvent(tick, timestamp, bpm, proximal_bpm_event_index=proximal_bpm_event_index)
