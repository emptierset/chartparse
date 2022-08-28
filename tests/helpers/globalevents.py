import pytest

from chartparse.globalevents import GlobalEvent, GlobalEventsTrack


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
    return GlobalEvent(tick, timestamp, value, proximal_bpm_event_index=proximal_bpm_event_index)
