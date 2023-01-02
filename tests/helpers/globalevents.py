import pytest

from chartparse.globalevents import (
    GlobalEvent,
    GlobalEventsTrack,
    TextEvent,
    SectionEvent,
    LyricEvent,
)


def GlobalEventsTrackWithDefaults(
    *,
    resolution=pytest.defaults.resolution,
    text_events=pytest.defaults.text_events,
    section_events=pytest.defaults.section_events,
    lyric_events=pytest.defaults.lyric_events,
):
    return GlobalEventsTrack(resolution, text_events, section_events, lyric_events)


def GlobalEventWithDefaults(
    *,
    tick=pytest.defaults.tick,
    timestamp=pytest.defaults.timestamp,
    value=pytest.defaults.global_event_value,
    proximal_bpm_event_index=pytest.defaults.proximal_bpm_event_index,
):
    return GlobalEvent(
        tick=tick,
        timestamp=timestamp,
        value=value,
        _proximal_bpm_event_index=proximal_bpm_event_index,
    )


def GlobalEventParsedDataWithDefaults(
    *,
    tick=pytest.defaults.tick,
    value=pytest.defaults.global_event_value,
):
    return GlobalEvent.ParsedData(tick=tick, value=value)


def TextEventParsedDataWithDefaults(
    *,
    tick=pytest.defaults.tick,
    value=pytest.defaults.text_event_value,
):
    return TextEvent.ParsedData(tick=tick, value=value)


def SectionEventParsedDataWithDefaults(
    *,
    tick=pytest.defaults.tick,
    value=pytest.defaults.section_event_value,
):
    return SectionEvent.ParsedData(tick=tick, value=value)


def LyricEventParsedDataWithDefaults(
    *,
    tick=pytest.defaults.tick,
    value=pytest.defaults.lyric_event_value,
):
    return LyricEvent.ParsedData(tick=tick, value=value)
