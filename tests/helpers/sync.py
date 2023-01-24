from __future__ import annotations

from chartparse.sync import AnchorEvent, BPMEvent, BPMEvents, SyncTrack, TimeSignatureEvent
from tests.helpers import defaults


def SyncTrackWithDefaults(
    *,
    time_signature_events=[defaults.time_signature_event],
    bpm_events=[defaults.bpm_event],
    anchor_events=[defaults.anchor_event],
):
    return SyncTrack(
        time_signature_events=time_signature_events,
        bpm_events=bpm_events,
        anchor_events=anchor_events,
    )


def TimeSignatureEventWithDefaults(
    *,
    tick=defaults.tick,
    timestamp=defaults.timestamp,
    upper_numeral=defaults.upper_time_signature_numeral,
    lower_numeral=defaults.lower_time_signature_numeral,
    proximal_bpm_event_index=defaults.proximal_bpm_event_index,
):
    return TimeSignatureEvent(
        tick=tick,
        timestamp=timestamp,
        upper_numeral=upper_numeral,
        lower_numeral=lower_numeral,
        _proximal_bpm_event_index=proximal_bpm_event_index,
    )


def TimeSignatureEventParsedDataWithDefaults(
    *, tick=defaults.tick, upper=defaults.upper_time_signature_numeral, lower=None
):
    return TimeSignatureEvent.ParsedData(tick=tick, upper=upper, lower=lower)


def BPMEventWithDefaults(
    *,
    tick=defaults.tick,
    timestamp=defaults.timestamp,
    bpm=defaults.bpm,
    proximal_bpm_event_index=defaults.proximal_bpm_event_index,
):
    return BPMEvent(
        tick=tick, timestamp=timestamp, bpm=bpm, _proximal_bpm_event_index=proximal_bpm_event_index
    )


def BPMEventParsedDataWithDefaults(
    *,
    tick=defaults.tick,
    raw_bpm=defaults.raw_bpm,
):
    return BPMEvent.ParsedData(tick=tick, raw_bpm=raw_bpm)


def BPMEventsWithDefaults(
    *,
    events=[defaults.bpm_event],
    resolution=defaults.resolution,
):
    return BPMEvents(events=events, resolution=resolution)


def AnchorEventWithDefaults(*, tick=defaults.tick, timestamp=defaults.timestamp):
    return AnchorEvent(tick=tick, timestamp=timestamp)


def AnchorEventParsedDataWithDefaults(*, tick=defaults.tick, microseconds=defaults.microseconds):
    return AnchorEvent.ParsedData(tick=tick, microseconds=microseconds)
