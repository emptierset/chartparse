from __future__ import annotations

import pytest

from chartparse.instrument import (
    StarPowerEvent,
    NoteEvent,
    SpecialEvent,
    InstrumentTrack,
    TrackEvent,
)


def InstrumentTrackWithDefaults(
    *,
    resolution=pytest.defaults.resolution,
    instrument=pytest.defaults.instrument,
    difficulty=pytest.defaults.difficulty,
    note_events=pytest.defaults.note_events,
    star_power_events=pytest.defaults.star_power_events,
    track_events=pytest.defaults.track_events,
):
    return InstrumentTrack(
        resolution=resolution,
        instrument=instrument,
        difficulty=difficulty,
        note_events=note_events,
        star_power_events=star_power_events,
        track_events=track_events,
    )


def SpecialEventWithDefaults(
    *,
    tick=pytest.defaults.tick,
    timestamp=pytest.defaults.timestamp,
    sustain=pytest.defaults.sustain,
    proximal_bpm_event_index=pytest.defaults.proximal_bpm_event_index,
    init_end_tick=False,
):
    s = SpecialEvent(
        tick=tick,
        timestamp=timestamp,
        sustain=sustain,
        _proximal_bpm_event_index=proximal_bpm_event_index,
    )
    if init_end_tick:
        s.end_tick  # accessing this initializes it because it's a cached_property
    return s


def SpecialEventParsedDataWithDefaults(
    *,
    tick=pytest.defaults.tick,
    sustain=pytest.defaults.sustain,
):
    return SpecialEvent.ParsedData(tick=tick, sustain=sustain)


def StarPowerEventWithDefaults(
    *,
    tick=pytest.defaults.tick,
    timestamp=pytest.defaults.timestamp,
    sustain=pytest.defaults.sustain,
    proximal_bpm_event_index=pytest.defaults.proximal_bpm_event_index,
    init_end_tick=False,
):
    s = StarPowerEvent(
        tick=tick,
        timestamp=timestamp,
        sustain=sustain,
        _proximal_bpm_event_index=proximal_bpm_event_index,
    )
    if init_end_tick:
        s.end_tick  # accessing this initializes it because it's a cached_property
    return s


def NoteEventWithDefaults(
    *,
    tick=pytest.defaults.tick,
    timestamp=pytest.defaults.timestamp,
    end_timestamp=pytest.defaults.timestamp,
    note=pytest.defaults.note,
    hopo_state=pytest.defaults.hopo_state,
    sustain=pytest.defaults.sustain,
    star_power_data=None,
    proximal_bpm_event_index=pytest.defaults.proximal_bpm_event_index,
):
    return NoteEvent(
        tick=tick,
        timestamp=timestamp,
        end_timestamp=end_timestamp,
        note=note,
        hopo_state=hopo_state,
        sustain=sustain,
        star_power_data=star_power_data,
        _proximal_bpm_event_index=proximal_bpm_event_index,
    )


def NoteEventParsedDataWithDefaults(
    *,
    tick=pytest.defaults.tick,
    note_track_index=pytest.defaults.note_track_index,
    sustain=pytest.defaults.sustain_list,
):
    return NoteEvent.ParsedData(
        tick=tick,
        note_track_index=note_track_index,
        sustain=sustain,
    )


def TrackEventWithDefaults(
    *,
    tick=pytest.defaults.tick,
    timestamp=pytest.defaults.timestamp,
    value=pytest.defaults.global_event_value,
    proximal_bpm_event_index=pytest.defaults.proximal_bpm_event_index,
):
    return TrackEvent(
        tick=tick,
        timestamp=timestamp,
        value=value,
        _proximal_bpm_event_index=proximal_bpm_event_index,
    )


def TrackEventParsedDataWithDefaults(
    *,
    tick=pytest.defaults.tick,
    value=pytest.defaults.track_event_value,
):
    return TrackEvent.ParsedData(tick=tick, value=value)
