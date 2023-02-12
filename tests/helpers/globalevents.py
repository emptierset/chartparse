from collections.abc import Sequence
from datetime import timedelta

from chartparse.globalevents import (
    GlobalEvent,
    GlobalEventsTrack,
    LyricEvent,
    SectionEvent,
    TextEvent,
)
from chartparse.tick import Tick
from chartparse.time import Timestamp
from tests.helpers import defaults


def GlobalEventsTrackWithDefaults(
    *,
    text_events: Sequence[TextEvent] = [defaults.text_event],
    section_events: Sequence[SectionEvent] = [defaults.section_event],
    lyric_events: Sequence[LyricEvent] = [defaults.lyric_event],
) -> GlobalEventsTrack:
    return GlobalEventsTrack(
        text_events=text_events,
        section_events=section_events,
        lyric_events=lyric_events,
    )


def GlobalEventWithDefaults(
    *,
    tick: Tick | int = defaults.tick,
    timestamp: Timestamp | timedelta = defaults.timestamp,
    value: str = defaults.global_event_value,
    _proximal_bpm_event_index: int = defaults.proximal_bpm_event_index,
) -> GlobalEvent:
    return GlobalEvent(
        tick=Tick(tick),
        timestamp=Timestamp(timestamp),
        value=value,
        _proximal_bpm_event_index=_proximal_bpm_event_index,
    )


def GlobalEventParsedDataWithDefaults(
    *,
    tick: Tick | int = defaults.tick,
    value: str = defaults.global_event_value,
) -> GlobalEvent.ParsedData:
    return GlobalEvent.ParsedData(tick=Tick(tick), value=value)


def TextEventParsedDataWithDefaults(
    *,
    tick: Tick | int = defaults.tick,
    value: str = defaults.text_event_value,
) -> TextEvent.ParsedData:
    return TextEvent.ParsedData(tick=Tick(tick), value=value)


def SectionEventParsedDataWithDefaults(
    *,
    tick: Tick | int = defaults.tick,
    value: str = defaults.section_event_value,
) -> SectionEvent.ParsedData:
    return SectionEvent.ParsedData(tick=Tick(tick), value=value)


def LyricEventParsedDataWithDefaults(
    *,
    tick: Tick | int = defaults.tick,
    value: str = defaults.lyric_event_value,
) -> LyricEvent.ParsedData:
    return LyricEvent.ParsedData(tick=Tick(tick), value=value)
