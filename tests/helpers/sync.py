from __future__ import annotations

import pytest

from chartparse.sync import TimeSignatureEvent, BPMEvent, SyncTrack, AnchorEvent


def SyncTrackWithDefaults(
    *,
    resolution=pytest.defaults.resolution,
    time_signature_events=pytest.defaults.time_signature_events,
    bpm_events=pytest.defaults.bpm_events,
    anchor_events=pytest.defaults.anchor_events,
):
    return SyncTrack(
        resolution=resolution,
        time_signature_events=time_signature_events,
        bpm_events=bpm_events,
        anchor_events=anchor_events,
    )


def TimeSignatureEventWithDefaults(
    *,
    tick=pytest.defaults.tick,
    timestamp=pytest.defaults.timestamp,
    upper_numeral=pytest.defaults.upper_time_signature_numeral,
    lower_numeral=pytest.defaults.lower_time_signature_numeral,
    proximal_bpm_event_index=pytest.defaults.proximal_bpm_event_index,
):
    return TimeSignatureEvent(
        tick=tick,
        timestamp=timestamp,
        upper_numeral=upper_numeral,
        lower_numeral=lower_numeral,
        _proximal_bpm_event_index=proximal_bpm_event_index,
    )


def TimeSignatureEventParsedDataWithDefaults(
    *, tick=pytest.defaults.tick, upper=pytest.defaults.upper_time_signature_numeral, lower=None
):
    return TimeSignatureEvent.ParsedData(tick=tick, upper=upper, lower=lower)


def BPMEventWithDefaults(
    *,
    tick=pytest.defaults.tick,
    timestamp=pytest.defaults.timestamp,
    bpm=pytest.defaults.bpm,
    proximal_bpm_event_index=pytest.defaults.proximal_bpm_event_index,
):
    return BPMEvent(
        tick=tick, timestamp=timestamp, bpm=bpm, _proximal_bpm_event_index=proximal_bpm_event_index
    )


def BPMEventParsedDataWithDefaults(
    *,
    tick=pytest.defaults.tick,
    raw_bpm=pytest.defaults.raw_bpm,
):
    return BPMEvent.ParsedData(tick=tick, raw_bpm=raw_bpm)


def AnchorEventWithDefaults(*, tick=pytest.defaults.tick, timestamp=pytest.defaults.timestamp):
    return AnchorEvent(tick=tick, timestamp=timestamp)


def AnchorEventParsedDataWithDefaults(
    *, tick=pytest.defaults.tick, microseconds=pytest.defaults.microseconds
):
    return AnchorEvent.ParsedData(tick=tick, microseconds=microseconds)
