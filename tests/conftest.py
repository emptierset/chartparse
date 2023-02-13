from __future__ import annotations

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "helpers"))

import typing as typ

import pytest

from chartparse.chart import Chart, InstrumentTrackMap
from chartparse.event import Event
from chartparse.globalevents import (
    GlobalEvent,
    GlobalEventsTrack,
    LyricEvent,
    SectionEvent,
    TextEvent,
)
from chartparse.instrument import (
    InstrumentTrack,
    NoteEvent,
    SpecialEvent,
    StarPowerEvent,
    TrackEvent,
)
from chartparse.metadata import Metadata
from chartparse.sync import AnchorEvent, BPMEvent, BPMEvents, SyncTrack, TimeSignatureEvent
from chartparse.tick import Tick
from chartparse.time import Timestamp
from tests.helpers import defaults, unsafe
from tests.helpers.sync import BPMEventsWithMock


@pytest.fixture
def invalid_chart_line() -> str:
    return defaults.invalid_chart_line


# chart.py object fixtures


@pytest.fixture
def minimal_instrument_tracks(minimal_instrument_track: InstrumentTrack) -> InstrumentTrackMap:
    return InstrumentTrackMap(
        {defaults.instrument: {defaults.difficulty: minimal_instrument_track}}
    )


@pytest.fixture
def default_instrument_tracks(default_instrument_track: InstrumentTrack) -> InstrumentTrackMap:
    return InstrumentTrackMap(
        {defaults.instrument: {defaults.difficulty: default_instrument_track}}
    )


@pytest.fixture
def bare_chart() -> Chart:
    return Chart.__new__(Chart)


@pytest.fixture
def minimal_chart(
    bare_chart: Chart,
    minimal_metadata: Metadata,
    minimal_instrument_tracks: InstrumentTrackMap,
    minimal_sync_track: SyncTrack,
    minimal_global_events_track: GlobalEventsTrack,
) -> Chart:
    """Minimal initialization necessary to avoid attribute errors."""
    unsafe.setattr(bare_chart, "metadata", minimal_metadata)
    unsafe.setattr(bare_chart, "sync_track", minimal_sync_track)
    unsafe.setattr(bare_chart, "global_events_track", minimal_global_events_track)
    unsafe.setattr(bare_chart, "instrument_tracks", minimal_instrument_tracks)
    return bare_chart


@pytest.fixture
def default_chart(
    default_metadata: Metadata,
    default_global_events_track: GlobalEventsTrack,
    default_sync_track: SyncTrack,
    default_instrument_tracks: InstrumentTrackMap,
) -> Chart:
    return Chart(
        default_metadata,
        default_global_events_track,
        default_sync_track,
        default_instrument_tracks,
    )


# event.py object fixtures


@pytest.fixture
def bare_event() -> Event:
    return Event.__new__(Event)


@pytest.fixture
def default_event() -> Event:
    return Event(tick=defaults.tick, timestamp=defaults.timestamp)


# instrument.py object fixtures


@pytest.fixture
def bare_instrument_track() -> InstrumentTrack:
    return InstrumentTrack.__new__(InstrumentTrack)


@pytest.fixture
def minimal_instrument_track(bare_instrument_track: InstrumentTrack) -> InstrumentTrack:
    """Minimal initialization necessary to avoid attribute errors."""
    unsafe.setattr(bare_instrument_track, "instrument", defaults.instrument)
    unsafe.setattr(bare_instrument_track, "difficulty", defaults.difficulty)
    unsafe.setattr(bare_instrument_track, "section_name", "ExpertSingle")
    unsafe.setattr(bare_instrument_track, "note_events", [])
    unsafe.setattr(bare_instrument_track, "star_power_events", [])
    return bare_instrument_track


@pytest.fixture
def default_instrument_track() -> InstrumentTrack:
    return InstrumentTrack(
        instrument=defaults.instrument,
        difficulty=defaults.difficulty,
        note_events=[defaults.note_event],
        star_power_events=[defaults.star_power_event],
        track_events=[defaults.track_event],
    )


@pytest.fixture
def bare_note_event() -> NoteEvent:
    return NoteEvent.__new__(NoteEvent)


@pytest.fixture
def bare_note_event_parsed_data() -> NoteEvent.ParsedData:
    return NoteEvent.ParsedData.__new__(NoteEvent.ParsedData)


@pytest.fixture
def default_note_event() -> NoteEvent:
    return defaults.note_event


@pytest.fixture
def bare_special_event() -> SpecialEvent:
    return SpecialEvent.__new__(SpecialEvent)


@pytest.fixture
def default_special_event() -> SpecialEvent:
    return SpecialEvent(tick=defaults.tick, timestamp=defaults.timestamp, sustain=defaults.sustain)


@pytest.fixture
def bare_star_power_event() -> StarPowerEvent:
    return StarPowerEvent.__new__(StarPowerEvent)


@pytest.fixture
def default_star_power_event() -> StarPowerEvent:
    return defaults.star_power_event


@pytest.fixture
def bare_track_event() -> TrackEvent:
    return TrackEvent.__new__(TrackEvent)


@pytest.fixture
def default_track_event() -> TrackEvent:
    return defaults.track_event


# sync.py object fixtures


@pytest.fixture
def bare_sync_track() -> SyncTrack:
    return SyncTrack.__new__(SyncTrack)


@pytest.fixture
def minimal_sync_track(bare_sync_track: SyncTrack, bare_bpm_events: BPMEvents) -> SyncTrack:
    """Minimal initialization necessary to avoid attribute errors."""
    unsafe.setattr(bare_sync_track, "anchor_events", [])
    unsafe.setattr(bare_sync_track, "time_signature_events", [])
    unsafe.setattr(bare_sync_track, "bpm_events", bare_bpm_events)
    return bare_sync_track


@pytest.fixture
def default_sync_track() -> SyncTrack:
    return SyncTrack(
        time_signature_events=[defaults.time_signature_event],
        bpm_events=defaults.bpm_events,
        anchor_events=[defaults.anchor_event],
    )


@pytest.fixture
def bare_time_signature_event() -> TimeSignatureEvent:
    return TimeSignatureEvent.__new__(TimeSignatureEvent)


@pytest.fixture
def default_time_signature_event() -> TimeSignatureEvent:
    return defaults.time_signature_event


@pytest.fixture
def bare_bpm_event() -> BPMEvent:
    return BPMEvent.__new__(BPMEvent)


@pytest.fixture
def default_bpm_event() -> BPMEvent:
    return defaults.bpm_event


@pytest.fixture
def bare_bpm_events() -> BPMEvents:
    return BPMEvents.__new__(BPMEvents)


@pytest.fixture
def minimal_bpm_events(bare_bpm_events: BPMEvents) -> BPMEvents:
    unsafe.setattr(bare_bpm_events, "events", [])
    unsafe.setattr(bare_bpm_events, "resolution", defaults.resolution)
    return bare_bpm_events


@pytest.fixture
def minimal_bpm_events_with_mock(
    mocker: typ.Any, minimal_bpm_events: BPMEvents
) -> BPMEventsWithMock:
    class SpyableClass(object):
        def timestamp_at_tick(
            self, tick: Tick, *, start_iteration_index: int = 0
        ) -> tuple[Timestamp, int]:
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
    assert isinstance(minimal_bpm_events, BPMEventsWithMock)
    return minimal_bpm_events


@pytest.fixture
def bare_anchor_event() -> AnchorEvent:
    return AnchorEvent.__new__(AnchorEvent)


@pytest.fixture
def default_anchor_event() -> AnchorEvent:
    return defaults.anchor_event


# globalevents.py object fixtures


@pytest.fixture
def bare_global_events_track() -> GlobalEventsTrack:
    return GlobalEventsTrack.__new__(GlobalEventsTrack)


@pytest.fixture
def minimal_global_events_track(bare_global_events_track: GlobalEventsTrack) -> GlobalEventsTrack:
    """Minimal initialization necessary to avoid attribute errors."""
    unsafe.setattr(bare_global_events_track, "text_events", [])
    unsafe.setattr(bare_global_events_track, "section_events", [])
    unsafe.setattr(bare_global_events_track, "lyric_events", [])
    return bare_global_events_track


@pytest.fixture
def default_global_events_track() -> GlobalEventsTrack:
    return GlobalEventsTrack(
        text_events=[defaults.text_event],
        section_events=[defaults.section_event],
        lyric_events=[defaults.lyric_event],
    )


@pytest.fixture
def bare_global_event() -> GlobalEvent:
    return GlobalEvent.__new__(GlobalEvent)


@pytest.fixture
def default_global_event() -> GlobalEvent:
    return defaults.global_event


@pytest.fixture
def bare_text_event() -> TextEvent:
    return TextEvent.__new__(TextEvent)


@pytest.fixture
def default_text_event() -> TextEvent:
    return defaults.text_event


@pytest.fixture
def bare_section_event() -> SectionEvent:
    return SectionEvent.__new__(SectionEvent)


@pytest.fixture
def default_section_event() -> SectionEvent:
    return defaults.section_event


@pytest.fixture
def bare_lyric_event() -> LyricEvent:
    return LyricEvent.__new__(LyricEvent)


@pytest.fixture
def default_lyric_event() -> LyricEvent:
    return defaults.lyric_event


# metadata.py object fixtures


@pytest.fixture
def bare_metadata() -> Metadata:
    return Metadata.__new__(Metadata)


@pytest.fixture
def minimal_metadata() -> Metadata:
    """Minimal initialization necessary to avoid attribute errors."""
    return Metadata(resolution=defaults.resolution)


@pytest.fixture
def default_metadata() -> Metadata:
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
