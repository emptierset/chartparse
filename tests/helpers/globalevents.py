from chartparse.globalevents import (
    GlobalEvent,
    GlobalEventsTrack,
    LyricEvent,
    SectionEvent,
    TextEvent,
)
from tests.helpers import defaults


def GlobalEventsTrackWithDefaults(
    *,
    resolution=defaults.resolution,
    text_events=[defaults.text_event],
    section_events=[defaults.section_event],
    lyric_events=[defaults.lyric_event],
):
    return GlobalEventsTrack(
        resolution=resolution,
        text_events=text_events,
        section_events=section_events,
        lyric_events=lyric_events,
    )


def GlobalEventWithDefaults(
    *,
    tick=defaults.tick,
    timestamp=defaults.timestamp,
    value=defaults.global_event_value,
    proximal_bpm_event_index=defaults.proximal_bpm_event_index,
):
    return GlobalEvent(
        tick=tick,
        timestamp=timestamp,
        value=value,
        _proximal_bpm_event_index=proximal_bpm_event_index,
    )


def GlobalEventParsedDataWithDefaults(
    *,
    tick=defaults.tick,
    value=defaults.global_event_value,
):
    return GlobalEvent.ParsedData(tick=tick, value=value)


def TextEventParsedDataWithDefaults(
    *,
    tick=defaults.tick,
    value=defaults.text_event_value,
):
    return TextEvent.ParsedData(tick=tick, value=value)


def SectionEventParsedDataWithDefaults(
    *,
    tick=defaults.tick,
    value=defaults.section_event_value,
):
    return SectionEvent.ParsedData(tick=tick, value=value)


def LyricEventParsedDataWithDefaults(
    *,
    tick=defaults.tick,
    value=defaults.lyric_event_value,
):
    return LyricEvent.ParsedData(tick=tick, value=value)
