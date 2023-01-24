from __future__ import annotations


from chartparse.instrument import (
    StarPowerEvent,
    NoteEvent,
    SpecialEvent,
    InstrumentTrack,
    TrackEvent,
)

from tests.helpers import defaults


def InstrumentTrackWithDefaults(
    *,
    resolution=defaults.resolution,
    instrument=defaults.instrument,
    difficulty=defaults.difficulty,
    note_events=[defaults.note_event],
    star_power_events=[defaults.star_power_event],
    track_events=[defaults.track_event],
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
    tick=defaults.tick,
    timestamp=defaults.timestamp,
    sustain=defaults.sustain,
    proximal_bpm_event_index=defaults.proximal_bpm_event_index,
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
    tick=defaults.tick,
    sustain=defaults.sustain,
):
    return SpecialEvent.ParsedData(tick=tick, sustain=sustain)


def StarPowerEventWithDefaults(
    *,
    tick=defaults.tick,
    timestamp=defaults.timestamp,
    sustain=defaults.sustain,
    proximal_bpm_event_index=defaults.proximal_bpm_event_index,
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
    tick=defaults.tick,
    timestamp=defaults.timestamp,
    end_timestamp=defaults.timestamp,
    note=defaults.note,
    hopo_state=defaults.hopo_state,
    sustain=defaults.sustain,
    star_power_data=None,
    proximal_bpm_event_index=defaults.proximal_bpm_event_index,
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
    tick=defaults.tick,
    note_track_index=defaults.note_track_index,
    sustain=defaults.sustain_list,
):
    return NoteEvent.ParsedData(
        tick=tick,
        note_track_index=note_track_index,
        sustain=sustain,
    )


def TrackEventWithDefaults(
    *,
    tick=defaults.tick,
    timestamp=defaults.timestamp,
    value=defaults.global_event_value,
    proximal_bpm_event_index=defaults.proximal_bpm_event_index,
):
    return TrackEvent(
        tick=tick,
        timestamp=timestamp,
        value=value,
        _proximal_bpm_event_index=proximal_bpm_event_index,
    )


def TrackEventParsedDataWithDefaults(
    *,
    tick=defaults.tick,
    value=defaults.track_event_value,
):
    return TrackEvent.ParsedData(tick=tick, value=value)
