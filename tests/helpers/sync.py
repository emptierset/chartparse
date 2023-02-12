from __future__ import annotations

import typing as typ
from collections.abc import Sequence
from datetime import timedelta

from chartparse.sync import AnchorEvent, BPMEvent, BPMEvents, SyncTrack, TimeSignatureEvent
from chartparse.tick import Tick, Ticks
from chartparse.time import Timestamp
from tests.helpers import defaults


def SyncTrackWithDefaults(
    *,
    time_signature_events: Sequence[TimeSignatureEvent] = [defaults.time_signature_event],
    bpm_events: BPMEvents = defaults.bpm_events,
    anchor_events: Sequence[AnchorEvent] = [defaults.anchor_event],
) -> SyncTrack:
    return SyncTrack(
        time_signature_events=time_signature_events,
        bpm_events=bpm_events,
        anchor_events=anchor_events,
    )


def TimeSignatureEventWithDefaults(
    *,
    tick: Tick | int = defaults.tick,
    timestamp: Timestamp | timedelta = defaults.timestamp,
    upper_numeral: int = defaults.upper_time_signature_numeral,
    lower_numeral: int = defaults.lower_time_signature_numeral,
    _proximal_bpm_event_index: int = defaults.proximal_bpm_event_index,
) -> TimeSignatureEvent:
    return TimeSignatureEvent(
        tick=Tick(tick),
        timestamp=Timestamp(timestamp),
        upper_numeral=upper_numeral,
        lower_numeral=lower_numeral,
        _proximal_bpm_event_index=_proximal_bpm_event_index,
    )


def TimeSignatureEventParsedDataWithDefaults(
    *,
    tick: Tick | int = defaults.tick,
    upper: int = defaults.upper_time_signature_numeral,
    lower: int | None = None,
) -> TimeSignatureEvent.ParsedData:
    return TimeSignatureEvent.ParsedData(tick=Tick(tick), upper=upper, lower=lower)


def BPMEventWithDefaults(
    *,
    tick: Tick | int = defaults.tick,
    timestamp: Timestamp | timedelta = defaults.timestamp,
    bpm: float = defaults.bpm,
    _proximal_bpm_event_index: int = defaults.proximal_bpm_event_index,
) -> BPMEvent:
    return BPMEvent(
        tick=Tick(tick),
        timestamp=Timestamp(timestamp),
        bpm=bpm,
        _proximal_bpm_event_index=_proximal_bpm_event_index,
    )


def BPMEventParsedDataWithDefaults(
    *,
    tick: Tick | int = defaults.tick,
    raw_bpm: str = defaults.raw_bpm,
) -> BPMEvent.ParsedData:
    return BPMEvent.ParsedData(tick=Tick(tick), raw_bpm=raw_bpm)


@typ.runtime_checkable
class BPMEventsWithMock(typ.Protocol):
    resolution: Ticks

    timestamp: Timestamp
    proximal_bpm_event_index: int
    timestamp_at_tick_mock: typ.Any

    def timestamp_at_tick_no_optimize_return(
        self, tick: Tick, *, start_iteration_index: int = 0
    ) -> Timestamp:
        ...


def BPMEventsWithDefaults(
    *,
    events: Sequence[BPMEvent] = [defaults.bpm_event],
    resolution: Ticks | int = defaults.resolution,
) -> BPMEvents:
    return BPMEvents(events=events, resolution=Ticks(resolution))


def AnchorEventWithDefaults(
    *,
    tick: Tick | int = defaults.tick,
    timestamp: Timestamp | timedelta = defaults.timestamp,
) -> AnchorEvent:
    return AnchorEvent(tick=Tick(tick), timestamp=Timestamp(timestamp))


def AnchorEventParsedDataWithDefaults(
    *,
    tick: Tick | int = defaults.tick,
    microseconds: int = defaults.microseconds,
) -> AnchorEvent.ParsedData:
    return AnchorEvent.ParsedData(tick=Tick(tick), microseconds=microseconds)
