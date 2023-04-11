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
def minimal_chart(
    minimal_metadata: Metadata,
    minimal_instrument_tracks: InstrumentTrackMap,
    minimal_sync_track: SyncTrack,
    minimal_global_events_track: GlobalEventsTrack,
) -> Chart:
    c = Chart.__new__(Chart)
    unsafe.setattr(c, "metadata", minimal_metadata)
    unsafe.setattr(c, "sync_track", minimal_sync_track)
    unsafe.setattr(c, "global_events_track", minimal_global_events_track)
    unsafe.setattr(c, "instrument_tracks", minimal_instrument_tracks)
    return c


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
def minimal_event() -> Event:
    e = Event.__new__(Event)
    unsafe.setattr(e, "tick", None)
    unsafe.setattr(e, "timestamp", None)
    return e


@pytest.fixture
def default_event() -> Event:
    return Event(tick=defaults.tick, timestamp=defaults.timestamp)


# instrument.py object fixtures


@pytest.fixture
def minimal_instrument_track() -> InstrumentTrack:
    it = InstrumentTrack.__new__(InstrumentTrack)
    unsafe.setattr(it, "instrument", None)
    unsafe.setattr(it, "difficulty", None)
    unsafe.setattr(it, "header_tag", None)
    unsafe.setattr(it, "note_events", None)
    unsafe.setattr(it, "star_power_events", None)
    return it


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
def minimal_note_event() -> NoteEvent:
    e = NoteEvent.__new__(NoteEvent)
    unsafe.setattr(e, "tick", None)
    unsafe.setattr(e, "timestamp", None)
    unsafe.setattr(e, "note", None)
    unsafe.setattr(e, "end_timestamp", None)
    unsafe.setattr(e, "hopo_state", None)
    return e


@pytest.fixture
def minimal_note_event_parsed_data() -> NoteEvent.ParsedData:
    pd = NoteEvent.ParsedData.__new__(NoteEvent.ParsedData)
    unsafe.setattr(pd, "tick", None)
    unsafe.setattr(pd, "note_track_index", None)
    unsafe.setattr(pd, "sustain", None)
    return pd


@pytest.fixture
def default_note_event() -> NoteEvent:
    return defaults.note_event


@pytest.fixture
def minimal_special_event() -> SpecialEvent:
    e = SpecialEvent.__new__(SpecialEvent)
    unsafe.setattr(e, "tick", None)
    unsafe.setattr(e, "timestamp", None)
    unsafe.setattr(e, "sustain", None)
    return e


@pytest.fixture
def default_special_event() -> SpecialEvent:
    return SpecialEvent(tick=defaults.tick, timestamp=defaults.timestamp, sustain=defaults.sustain)


@pytest.fixture
def minimal_star_power_event() -> StarPowerEvent:
    e = StarPowerEvent.__new__(StarPowerEvent)
    unsafe.setattr(e, "tick", None)
    unsafe.setattr(e, "timestamp", None)
    unsafe.setattr(e, "sustain", None)
    return e


@pytest.fixture
def default_star_power_event() -> StarPowerEvent:
    return defaults.star_power_event


@pytest.fixture
def minimal_track_event() -> TrackEvent:
    e = TrackEvent.__new__(TrackEvent)
    unsafe.setattr(e, "tick", None)
    unsafe.setattr(e, "timestamp", None)
    unsafe.setattr(e, "value", None)
    return e


@pytest.fixture
def default_track_event() -> TrackEvent:
    return defaults.track_event


# sync.py object fixtures


@pytest.fixture
def minimal_sync_track(minimal_bpm_events: BPMEvents) -> SyncTrack:
    st = SyncTrack.__new__(SyncTrack)
    unsafe.setattr(st, "anchor_events", None)
    unsafe.setattr(st, "time_signature_events", None)
    unsafe.setattr(st, "bpm_events", minimal_bpm_events)
    return st


@pytest.fixture
def default_sync_track() -> SyncTrack:
    return SyncTrack(
        time_signature_events=[defaults.time_signature_event],
        bpm_events=defaults.bpm_events,
        anchor_events=[defaults.anchor_event],
    )


@pytest.fixture
def minimal_time_signature_event() -> TimeSignatureEvent:
    e = TimeSignatureEvent.__new__(TimeSignatureEvent)
    unsafe.setattr(e, "tick", None)
    unsafe.setattr(e, "timestamp", None)
    unsafe.setattr(e, "upper_numeral", None)
    unsafe.setattr(e, "lower_numeral", None)
    return e


@pytest.fixture
def default_time_signature_event() -> TimeSignatureEvent:
    return defaults.time_signature_event


@pytest.fixture
def minimal_bpm_event() -> BPMEvent:
    e = BPMEvent.__new__(BPMEvent)
    unsafe.setattr(e, "tick", None)
    unsafe.setattr(e, "timestamp", None)
    unsafe.setattr(e, "bpm", None)
    return e


@pytest.fixture
def default_bpm_event() -> BPMEvent:
    return defaults.bpm_event


@pytest.fixture
def minimal_bpm_events() -> BPMEvents:
    be = BPMEvents.__new__(BPMEvents)
    unsafe.setattr(be, "events", None)
    unsafe.setattr(be, "resolution", None)
    return be


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
def minimal_anchor_event() -> AnchorEvent:
    e = AnchorEvent.__new__(AnchorEvent)
    unsafe.setattr(e, "tick", None)
    unsafe.setattr(e, "timestamp", None)
    return e


@pytest.fixture
def default_anchor_event() -> AnchorEvent:
    return defaults.anchor_event


# globalevents.py object fixtures


@pytest.fixture
def minimal_global_events_track() -> GlobalEventsTrack:
    et = GlobalEventsTrack.__new__(GlobalEventsTrack)
    unsafe.setattr(et, "text_events", None)
    unsafe.setattr(et, "section_events", None)
    unsafe.setattr(et, "lyric_events", None)
    return et


@pytest.fixture
def default_global_events_track() -> GlobalEventsTrack:
    return GlobalEventsTrack(
        text_events=[defaults.text_event],
        section_events=[defaults.section_event],
        lyric_events=[defaults.lyric_event],
    )


@pytest.fixture
def minimal_global_event() -> GlobalEvent:
    e = GlobalEvent.__new__(GlobalEvent)
    unsafe.setattr(e, "tick", None)
    unsafe.setattr(e, "timestamp", None)
    unsafe.setattr(e, "value", None)
    return e


@pytest.fixture
def default_global_event() -> GlobalEvent:
    return defaults.global_event


@pytest.fixture
def minimal_text_event() -> TextEvent:
    e = TextEvent.__new__(TextEvent)
    unsafe.setattr(e, "tick", None)
    unsafe.setattr(e, "timestamp", None)
    unsafe.setattr(e, "value", None)
    return e


@pytest.fixture
def default_text_event() -> TextEvent:
    return defaults.text_event


@pytest.fixture
def minimal_section_event() -> SectionEvent:
    e = SectionEvent.__new__(SectionEvent)
    unsafe.setattr(e, "tick", None)
    unsafe.setattr(e, "timestamp", None)
    unsafe.setattr(e, "value", None)
    return e


@pytest.fixture
def default_section_event() -> SectionEvent:
    return defaults.section_event


@pytest.fixture
def minimal_lyric_event() -> LyricEvent:
    e = LyricEvent.__new__(LyricEvent)
    unsafe.setattr(e, "tick", None)
    unsafe.setattr(e, "timestamp", None)
    unsafe.setattr(e, "value", None)
    return e


@pytest.fixture
def default_lyric_event() -> LyricEvent:
    return defaults.lyric_event


# metadata.py object fixtures


@pytest.fixture
def minimal_metadata() -> Metadata:
    m = Metadata.__new__(Metadata)
    unsafe.setattr(m, "resolution", None)
    unsafe.setattr(m, "offset", None)
    unsafe.setattr(m, "player2", None)
    unsafe.setattr(m, "difficulty", None)
    unsafe.setattr(m, "preview_start", None)
    unsafe.setattr(m, "preview_end", None)
    unsafe.setattr(m, "genre", None)
    unsafe.setattr(m, "media_type", None)
    unsafe.setattr(m, "name", None)
    unsafe.setattr(m, "artist", None)
    unsafe.setattr(m, "charter", None)
    unsafe.setattr(m, "album", None)
    unsafe.setattr(m, "year", None)
    unsafe.setattr(m, "music_stream", None)
    unsafe.setattr(m, "guitar_stream", None)
    unsafe.setattr(m, "rhythm_stream", None)
    unsafe.setattr(m, "bass_stream", None)
    unsafe.setattr(m, "drum_stream", None)
    unsafe.setattr(m, "drum2_stream", None)
    unsafe.setattr(m, "drum3_stream", None)
    unsafe.setattr(m, "drum4_stream", None)
    unsafe.setattr(m, "vocal_stream", None)
    unsafe.setattr(m, "keys_stream", None)
    unsafe.setattr(m, "crowd_stream", None)
    return m


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
