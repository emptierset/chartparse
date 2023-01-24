from __future__ import annotations

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "helpers"))

import pytest

from chartparse.chart import Chart
from chartparse.event import Event
from chartparse.globalevents import (
    GlobalEventsTrack,
    GlobalEvent,
    TextEvent,
    SectionEvent,
    LyricEvent,
)
from chartparse.instrument import (
    InstrumentTrack,
    NoteEvent,
    StarPowerData,
    StarPowerEvent,
    SpecialEvent,
    TrackEvent,
)
from chartparse.metadata import Metadata
from chartparse.sync import SyncTrack, BPMEvent, BPMEvents, TimeSignatureEvent, AnchorEvent

from tests.helpers import defaults
from tests.helpers import unsafe


@pytest.fixture
def invalid_chart_line():
    return defaults.invalid_chart_line


@pytest.fixture
def minimal_compute_hopo_state_mock(mocker):
    return mocker.patch.object(NoteEvent, "_compute_hopo_state", return_value=defaults.hopo_state)


@pytest.fixture
def minimal_compute_star_power_data_mock(mocker):
    return mocker.patch.object(
        NoteEvent, "_compute_star_power_data", return_value=(StarPowerData(0), 0)
    )


@pytest.fixture(
    params=[
        # Base events
        "default_event",
        # Sync events
        "default_time_signature_event",
        "default_bpm_event",
        "default_anchor_event",
        # Global events
        "default_text_event",
        "default_section_event",
        "default_lyric_event",
        # Instrument events
        "default_note_event",
        "default_star_power_event",
        "default_track_event",
    ]
)
def all_events(request):
    return request.getfixturevalue(request.param)


# chart.py object fixtures


@pytest.fixture
def minimal_instrument_tracks(minimal_instrument_track):
    return {defaults.instrument: {defaults.difficulty: minimal_instrument_track}}


@pytest.fixture
def default_instrument_tracks(default_instrument_track):
    return {defaults.instrument: {defaults.difficulty: default_instrument_track}}


@pytest.fixture
def bare_chart():
    return Chart.__new__(Chart)


@pytest.fixture
def minimal_chart(
    bare_chart,
    minimal_metadata,
    minimal_instrument_tracks,
    minimal_sync_track,
    minimal_global_events_track,
):
    """Minimal initialization necessary to avoid attribute errors."""
    bare_chart.metadata = minimal_metadata
    bare_chart.sync_track = minimal_sync_track
    bare_chart.global_events_track = minimal_global_events_track
    bare_chart.instrument_tracks = minimal_instrument_tracks
    return bare_chart


@pytest.fixture
def default_chart(
    default_metadata,
    default_global_events_track,
    default_sync_track,
    default_instrument_tracks,
):
    return Chart(
        default_metadata,
        default_global_events_track,
        default_sync_track,
        default_instrument_tracks,
    )


# event.py object fixtures


@pytest.fixture
def bare_event():
    return Event.__new__(Event)


@pytest.fixture
def default_event():
    return Event(tick=defaults.tick, timestamp=defaults.timestamp)


# instrument.py object fixtures


@pytest.fixture
def bare_instrument_track():
    return InstrumentTrack.__new__(InstrumentTrack)


@pytest.fixture
def minimal_instrument_track(bare_instrument_track):
    """Minimal initialization necessary to avoid attribute errors."""
    unsafe.setattr(bare_instrument_track, "instrument", defaults.instrument)
    unsafe.setattr(bare_instrument_track, "difficulty", defaults.difficulty)
    unsafe.setattr(bare_instrument_track, "section_name", "ExpertSingle")
    unsafe.setattr(bare_instrument_track, "note_events", [])
    unsafe.setattr(bare_instrument_track, "star_power_events", [])
    return bare_instrument_track


@pytest.fixture
def default_instrument_track():
    return InstrumentTrack(
        resolution=defaults.resolution,
        instrument=defaults.instrument,
        difficulty=defaults.difficulty,
        note_events=[defaults.note_event],
        star_power_events=[defaults.star_power_event],
        track_events=[defaults.track_event],
    )


@pytest.fixture
def bare_note_event():
    return NoteEvent.__new__(NoteEvent)


@pytest.fixture
def bare_note_event_parsed_data():
    return NoteEvent.ParsedData.__new__(NoteEvent.ParsedData)


@pytest.fixture
def default_note_event():
    return defaults.note_event


@pytest.fixture
def bare_special_event():
    return SpecialEvent.__new__(SpecialEvent)


@pytest.fixture
def default_special_event():
    return SpecialEvent(defaults.tick, defaults.timestamp, defaults.sustain)


@pytest.fixture
def bare_star_power_event():
    return StarPowerEvent.__new__(StarPowerEvent)


@pytest.fixture
def default_star_power_event():
    return defaults.star_power_event


@pytest.fixture
def bare_track_event():
    return TrackEvent.__new__(TrackEvent)


@pytest.fixture
def default_track_event():
    return defaults.track_event


# sync.py object fixtures


@pytest.fixture
def bare_sync_track():
    return SyncTrack.__new__(SyncTrack)


@pytest.fixture
def minimal_sync_track(bare_sync_track, bare_bpm_events):
    """Minimal initialization necessary to avoid attribute errors."""
    unsafe.setattr(bare_sync_track, "anchor_events", [])
    unsafe.setattr(bare_sync_track, "time_signature_events", [])
    unsafe.setattr(bare_sync_track, "bpm_events", bare_bpm_events)
    return bare_sync_track


@pytest.fixture
def default_sync_track():
    return SyncTrack(
        time_signature_events=[defaults.time_signature_event],
        bpm_events=[defaults.bpm_event],
        anchor_events=[defaults.anchor_event],
    )


@pytest.fixture
def bare_time_signature_event():
    return TimeSignatureEvent.__new__(TimeSignatureEvent)


@pytest.fixture
def default_time_signature_event():
    return defaults.time_signature_event


@pytest.fixture
def bare_bpm_event():
    return BPMEvent.__new__(BPMEvent)


@pytest.fixture
def default_bpm_event():
    return defaults.bpm_event


@pytest.fixture
def bare_bpm_events():
    return BPMEvents.__new__(BPMEvents)


@pytest.fixture
def minimal_bpm_events(bare_bpm_events):
    unsafe.setattr(bare_bpm_events, "events", [])
    unsafe.setattr(bare_bpm_events, "resolution", defaults.resolution)
    return bare_bpm_events


@pytest.fixture
def minimal_bpm_events_with_mock(mocker, minimal_bpm_events):
    class SpyableClass(object):
        def timestamp_at_tick(self, tick, *, start_iteration_index=0):
            return (
                defaults.timestamp_at_tick_timestamp,
                defaults.timestamp_at_tick_proximal_bpm_event_index,
            )

    # It is not possible to mock a method of a frozen dataclass conventionally. Instead, we must
    # manually create a fake method, spy on that, and substitute it using unsafe setattr.
    s = SpyableClass()
    spy = mocker.spy(s, "timestamp_at_tick")

    unsafe.setattr(
        minimal_bpm_events,
        "timestamp",
        defaults.timestamp_at_tick_timestamp,
    )
    unsafe.setattr(
        minimal_bpm_events,
        "proximal_bpm_event_index",
        defaults.timestamp_at_tick_proximal_bpm_event_index,
    )
    unsafe.setattr(
        minimal_bpm_events,
        "timestamp_at_tick_mock",
        spy,
    )
    unsafe.setattr(
        minimal_bpm_events,
        "timestamp_at_tick",
        s.timestamp_at_tick,
    )
    return minimal_bpm_events


@pytest.fixture
def bare_anchor_event():
    return AnchorEvent.__new__(AnchorEvent)


@pytest.fixture
def default_anchor_event():
    return defaults.anchor_event


# globalevents.py object fixtures


@pytest.fixture
def bare_global_events_track():
    return GlobalEventsTrack.__new__(GlobalEventsTrack)


@pytest.fixture
def minimal_global_events_track(bare_global_events_track):
    """Minimal initialization necessary to avoid attribute errors."""
    unsafe.setattr(bare_global_events_track, "text_events", [])
    unsafe.setattr(bare_global_events_track, "section_events", [])
    unsafe.setattr(bare_global_events_track, "lyric_events", [])
    return bare_global_events_track


@pytest.fixture
def default_global_events_track():
    return GlobalEventsTrack(
        resolution=defaults.resolution,
        text_events=[defaults.text_event],
        section_events=[defaults.section_event],
        lyric_events=[defaults.lyric_event],
    )


@pytest.fixture
def bare_global_event():
    return GlobalEvent.__new__(GlobalEvent)


@pytest.fixture
def default_global_event():
    return defaults.global_event


@pytest.fixture
def bare_text_event():
    return TextEvent.__new__(TextEvent)


@pytest.fixture
def default_text_event():
    return defaults.text_event


@pytest.fixture
def bare_section_event():
    return SectionEvent.__new__(SectionEvent)


@pytest.fixture
def default_section_event():
    return defaults.section_event


@pytest.fixture
def bare_lyric_event():
    return LyricEvent.__new__(LyricEvent)


@pytest.fixture
def default_lyric_event():
    return defaults.lyric_event


# metadata.py object fixtures


@pytest.fixture
def bare_metadata():
    return Metadata.__new__(Metadata)


@pytest.fixture
def minimal_metadata():
    """Minimal initialization necessary to avoid attribute errors."""
    return Metadata(resolution=defaults.resolution)


@pytest.fixture
def default_metadata():
    return Metadata(
        resolution=defaults.resolution,
        offset=defaults.offset,
        player2=defaults.player2,
        difficulty=defaults.intensity,
        preview_start=defaults.preview_start,
        preview_end=defaults.preview_end,
        genre=defaults.genre,
        media_type=defaults.media_type,
        name=defaults.name,
        artist=defaults.artist,
        charter=defaults.charter,
        album=defaults.album,
        year=defaults.year,
        music_stream=defaults.music_stream,
        guitar_stream=defaults.guitar_stream,
        rhythm_stream=defaults.rhythm_stream,
        bass_stream=defaults.bass_stream,
        drum_stream=defaults.drum_stream,
        drum2_stream=defaults.drum2_stream,
        drum3_stream=defaults.drum3_stream,
        drum4_stream=defaults.drum4_stream,
        vocal_stream=defaults.vocal_stream,
        keys_stream=defaults.keys_stream,
        crowd_stream=defaults.crowd_stream,
    )
