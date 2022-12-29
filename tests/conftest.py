from __future__ import annotations

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "helpers"))

import dataclasses
import datetime
import math
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
    NoteTrackIndex,
    StarPowerData,
    StarPowerEvent,
    SpecialEvent,
    Instrument,
    Difficulty,
    Note,
    HOPOState,
)
from chartparse.metadata import Metadata, Player2Instrument
from chartparse.sync import SyncTrack, BPMEvent, TimeSignatureEvent, AnchorEvent


_invalid_chart_line = "this_line_is_invalid"
_invalid_chart_lines = [_invalid_chart_line]

_default_filepath = "/not/a/real/path"

_default_tick = 0

_default_timestamp = datetime.timedelta(0)

_default_seconds = 0
_default_microseconds = _default_seconds // 1000000

_default_proximal_bpm_event_index = 0
_default_proximal_star_power_event_index = 0

_default_tatter_timestamp = datetime.timedelta(seconds=834)
_default_tatter_bpm_event_index = 47

_default_bpm = 120.000
_default_raw_bpm = str(int(_default_bpm * 1000))
_default_bpm_event = BPMEvent(_default_tick, _default_timestamp, _default_bpm)
_default_bpm_events = [_default_bpm_event]
_default_bpm_event_parsed_data = BPMEvent.ParsedData(tick=_default_tick, raw_bpm=_default_raw_bpm)
_default_bpm_event_parsed_datas = [_default_bpm_event_parsed_data]

_default_upper_time_signature_numeral = 4
_default_lower_time_signature_numeral = 8
_default_raw_lower_time_signature_numeral = int(math.log(_default_lower_time_signature_numeral, 2))
_default_time_signature_event = TimeSignatureEvent(
    _default_tick,
    _default_timestamp,
    _default_upper_time_signature_numeral,
    _default_lower_time_signature_numeral,
)
_default_time_signature_events = [_default_time_signature_event]
_default_time_signature_event_parsed_data = TimeSignatureEvent.ParsedData(
    tick=_default_tick,
    upper=_default_upper_time_signature_numeral,
    lower=_default_lower_time_signature_numeral,
)
_default_time_signature_event_parsed_datas = [_default_time_signature_event_parsed_data]

_default_anchor_event = AnchorEvent(_default_tick, _default_timestamp)
_default_anchor_events = [_default_anchor_event]
_default_anchor_event_parsed_data = AnchorEvent.ParsedData(
    tick=_default_tick, microseconds=_default_microseconds
)
_default_anchor_event_parsed_datas = [_default_anchor_event_parsed_data]

_default_global_event_value = "default_global_event_value"
_default_global_event = GlobalEvent(_default_tick, _default_timestamp, _default_global_event_value)
_default_global_events = [_default_global_event]
_default_global_event_parsed_data = GlobalEvent.ParsedData(
    tick=_default_tick, value=_default_global_event_value
)
_default_global_event_parsed_datas = [_default_global_event_parsed_data]

_default_text_event_value = "default_text_event_value"
_default_text_event = TextEvent(_default_tick, _default_timestamp, _default_text_event_value)
_default_text_events = [_default_text_event]
_default_text_event_parsed_data = TextEvent.ParsedData(
    tick=_default_tick, value=_default_text_event_value
)
_default_text_event_parsed_datas = [_default_text_event_parsed_data]

_default_section_event_value = "default_section_event_value"
_default_section_event = SectionEvent(
    _default_tick, _default_timestamp, _default_section_event_value
)
_default_section_events = [_default_section_event]
_default_section_event_parsed_data = SectionEvent.ParsedData(
    tick=_default_tick, value=_default_section_event_value
)
_default_section_event_parsed_datas = [_default_section_event_parsed_data]

_default_lyric_event_value = "default_lyric_event_value"
_default_lyric_event = LyricEvent(_default_tick, _default_timestamp, _default_lyric_event_value)
_default_lyric_events = [_default_lyric_event]
_default_lyric_event_parsed_data = LyricEvent.ParsedData(
    tick=_default_tick, value=_default_lyric_event_value
)
_default_lyric_event_parsed_datas = [_default_lyric_event_parsed_data]


_default_difficulty = Difficulty.EXPERT
_default_instrument = Instrument.GUITAR
_default_section_name = _default_difficulty.value + _default_instrument.value
_default_sustain = 0  # ticks
_default_sustain_list = [0, None, None, None, None]
_default_sustain_tuple = (0, None, None, None, None)

_default_note = Note.G
_default_note_track_index = NoteTrackIndex.G

_default_hopo_state = HOPOState.STRUM

_default_note_event = NoteEvent(
    _default_tick, _default_timestamp, _default_timestamp, _default_note, _default_hopo_state
)
_default_note_events = [_default_note_event]
_default_note_event_parsed_data = NoteEvent.ParsedData(
    tick=_default_tick,
    sustain=_default_sustain,
    note_track_index=_default_note_track_index,
)
_default_note_event_parsed_datas = [_default_note_event_parsed_data]

_default_star_power_event = StarPowerEvent(_default_tick, _default_timestamp, _default_sustain)
_default_star_power_events = [_default_star_power_event]
_default_star_power_event_parsed_data = StarPowerEvent.ParsedData(
    tick=_default_tick, sustain=_default_sustain
)
_default_star_power_event_parsed_datas = [_default_star_power_event_parsed_data]

_default_name = "Song Name"
_default_artist = "Artist Name"
_default_charter = "Charter Name"
_default_album = "Album Name"
_default_year = "1999"
_default_offset = 0
_default_offset_string = str(_default_offset)
_default_resolution = 192
_default_resolution_string = str(_default_resolution)
_default_player2 = Player2Instrument.BASS
_default_player2_string = _default_player2.value
_default_intensity = 2
_default_intensity_string = str(_default_intensity)
_default_preview_start = 3
_default_preview_start_string = str(_default_preview_start)
_default_preview_end = 4
_default_preview_end_string = str(_default_preview_end)
_default_genre = "metal"
_default_media_type = "vinyl"
_default_music_stream = "song.ogg"
_default_guitar_stream = "guitar.ogg"
_default_rhythm_stream = "rhythm.ogg"
_default_bass_stream = "bass.ogg"
_default_drum_stream = "drum.ogg"
_default_drum2_stream = "drum2.ogg"
_default_drum3_stream = "drum3.ogg"
_default_drum4_stream = "drum4.ogg"
_default_vocal_stream = "vocal.ogg"
_default_keys_stream = "keys.ogg"
_default_crowd_stream = "crowd.ogg"

# https://stackoverflow.com/a/1845097
_unmatchable_regex = r"(?!x)x"


@dataclasses.dataclass
class Defaults(object):
    filepath: ...

    tick: ...
    sustain: ...
    sustain_list: ...
    sustain_tuple: ...

    timestamp: ...

    seconds: ...
    microseconds: ...

    proximal_bpm_event_index: ...
    proximal_star_power_event_index: ...

    # TODO: Remove redundant "default" from names.
    default_tatter_timestamp: ...
    default_tatter_index: ...

    name: ...
    artist: ...
    charter: ...
    album: ...
    year: ...
    offset: ...
    offset_string: ...
    resolution: ...
    resolution_string: ...
    player2: ...
    player2_string: ...
    intensity: ...
    intensity_string: ...
    preview_start: ...
    preview_start_string: ...
    preview_end: ...
    preview_end_string: ...
    genre: ...
    media_type: ...
    music_stream: ...
    guitar_stream: ...
    rhythm_stream: ...
    bass_stream: ...
    drum_stream: ...
    drum2_stream: ...
    drum3_stream: ...
    drum4_stream: ...
    vocal_stream: ...
    keys_stream: ...
    crowd_stream: ...

    bpm: ...
    raw_bpm: ...
    bpm_event: ...
    bpm_events: ...
    bpm_event_parsed_data: ...
    bpm_event_parsed_datas: ...

    upper_time_signature_numeral: ...
    lower_time_signature_numeral: ...
    raw_lower_time_signature_numeral: ...
    time_signature_event: ...
    time_signature_events: ...
    time_signature_event_parsed_data: ...
    time_signature_event_parsed_datas: ...

    anchor_event: ...
    anchor_events: ...
    anchor_event_parsed_data: ...
    anchor_event_parsed_datas: ...

    global_event_value: ...
    text_event_value: ...
    section_event_value: ...
    lyric_event_value: ...
    text_event: ...
    section_event: ...
    lyric_event: ...
    text_event_parsed_data: ...
    section_event_parsed_data: ...
    lyric_event_parsed_data: ...
    text_events: ...
    section_events: ...
    lyric_events: ...
    text_event_parsed_datas: ...
    section_event_parsed_datas: ...
    lyric_event_parsed_datas: ...

    instrument: ...
    difficulty: ...
    section_name: ...

    hopo_state: ...

    note_track_index: ...
    note: ...
    note_event: ...
    note_events: ...
    note_event_parsed_data: ...
    note_event_parsed_datas: ...

    star_power_event: ...
    star_power_events: ...
    star_power_event_parsed_data: ...
    star_power_event_parsed_datas: ...


def pytest_configure():
    pytest.invalid_chart_line = _invalid_chart_line
    pytest.invalid_chart_lines = _invalid_chart_lines
    pytest.unmatchable_regex = _unmatchable_regex
    pytest.defaults = Defaults(
        filepath=_default_filepath,
        tick=_default_tick,
        sustain=_default_sustain,
        sustain_list=_default_sustain_list,
        sustain_tuple=_default_sustain_tuple,
        timestamp=_default_timestamp,
        seconds=_default_seconds,
        microseconds=_default_microseconds,
        proximal_bpm_event_index=_default_proximal_bpm_event_index,
        proximal_star_power_event_index=_default_proximal_star_power_event_index,
        default_tatter_timestamp=_default_tatter_timestamp,
        default_tatter_index=_default_tatter_bpm_event_index,
        name=_default_name,
        artist=_default_artist,
        charter=_default_charter,
        album=_default_album,
        year=_default_year,
        offset=_default_offset,
        offset_string=_default_offset_string,
        resolution=_default_resolution,
        resolution_string=_default_resolution_string,
        player2=_default_player2,
        player2_string=_default_player2_string,
        intensity=_default_intensity,
        intensity_string=_default_intensity_string,
        preview_start=_default_preview_start,
        preview_start_string=_default_preview_start_string,
        preview_end=_default_preview_end,
        preview_end_string=_default_preview_end_string,
        genre=_default_genre,
        media_type=_default_media_type,
        music_stream=_default_music_stream,
        guitar_stream=_default_guitar_stream,
        rhythm_stream=_default_rhythm_stream,
        bass_stream=_default_bass_stream,
        drum_stream=_default_drum_stream,
        drum2_stream=_default_drum2_stream,
        drum3_stream=_default_drum3_stream,
        drum4_stream=_default_drum4_stream,
        vocal_stream=_default_vocal_stream,
        keys_stream=_default_keys_stream,
        crowd_stream=_default_crowd_stream,
        bpm=_default_bpm,
        raw_bpm=_default_raw_bpm,
        bpm_event=_default_bpm_event,
        bpm_events=_default_bpm_events,
        bpm_event_parsed_data=_default_bpm_event_parsed_data,
        bpm_event_parsed_datas=_default_bpm_event_parsed_datas,
        upper_time_signature_numeral=_default_upper_time_signature_numeral,
        lower_time_signature_numeral=_default_lower_time_signature_numeral,
        raw_lower_time_signature_numeral=_default_raw_lower_time_signature_numeral,
        time_signature_event=_default_time_signature_event,
        time_signature_events=_default_time_signature_events,
        time_signature_event_parsed_data=_default_time_signature_event_parsed_data,
        time_signature_event_parsed_datas=_default_time_signature_event_parsed_datas,
        anchor_event=_default_anchor_event,
        anchor_events=_default_anchor_events,
        anchor_event_parsed_data=_default_anchor_event_parsed_data,
        anchor_event_parsed_datas=_default_anchor_event_parsed_datas,
        global_event_value=_default_global_event_value,
        text_event_value=_default_text_event_value,
        text_event=_default_text_event,
        text_events=_default_text_events,
        text_event_parsed_data=_default_text_event_parsed_data,
        text_event_parsed_datas=_default_text_event_parsed_datas,
        section_event_value=_default_section_event_value,
        section_event=_default_section_event,
        section_events=_default_section_events,
        section_event_parsed_data=_default_section_event_parsed_data,
        section_event_parsed_datas=_default_section_event_parsed_datas,
        lyric_event_value=_default_lyric_event_value,
        lyric_event=_default_lyric_event,
        lyric_events=_default_lyric_events,
        lyric_event_parsed_data=_default_lyric_event_parsed_data,
        lyric_event_parsed_datas=_default_lyric_event_parsed_datas,
        instrument=_default_instrument,
        difficulty=_default_difficulty,
        section_name=_default_section_name,
        hopo_state=_default_hopo_state,
        note_track_index=_default_note_track_index,
        note=_default_note,
        note_event=_default_note_event,
        note_events=_default_note_events,
        note_event_parsed_data=_default_note_event_parsed_data,
        note_event_parsed_datas=_default_note_event_parsed_datas,
        star_power_event=_default_star_power_event,
        star_power_events=_default_star_power_events,
        star_power_event_parsed_data=_default_star_power_event_parsed_data,
        star_power_event_parsed_datas=_default_star_power_event_parsed_datas,
    )


@pytest.fixture
def invalid_chart_line():
    return _invalid_chart_line


@pytest.fixture
def default_tatter(mocker):
    class FakeTimestampAtTicker(object):
        def __init__(self, resolution: int):
            self.resolution = resolution
            self.spy = mocker.spy(self, "timestamp_at_tick")

        def timestamp_at_tick(self, tick, proximal_bpm_event_index=0):
            return _default_tatter_timestamp, _default_tatter_bpm_event_index

    return FakeTimestampAtTicker(_default_resolution)


@pytest.fixture
def minimal_compute_hopo_state_mock(mocker):
    return mocker.patch.object(NoteEvent, "_compute_hopo_state", return_value=_default_hopo_state)


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
        # Global events
        "default_text_event",
        "default_section_event",
        "default_lyric_event",
        # Instrument events
        "default_note_event",
        "default_star_power_event",
    ]
)
def all_events(request):
    return request.getfixturevalue(request.param)


# chart.py object fixtures


@pytest.fixture
def minimal_instrument_tracks(minimal_instrument_track):
    return {_default_instrument: {_default_difficulty: minimal_instrument_track}}


@pytest.fixture
def default_instrument_tracks(default_instrument_track):
    return {_default_instrument: {_default_difficulty: default_instrument_track}}


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
    return Event(_default_tick, _default_timestamp)


# instrument.py object fixtures


@pytest.fixture
def bare_instrument_track():
    return InstrumentTrack.__new__(InstrumentTrack)


@pytest.fixture
def minimal_instrument_track(bare_instrument_track):
    """Minimal initialization necessary to avoid attribute errors."""
    bare_instrument_track.instrument = _default_instrument
    bare_instrument_track.difficulty = _default_difficulty
    bare_instrument_track.section_name = "ExpertSingle"
    bare_instrument_track.note_events = []
    bare_instrument_track.star_power_events = []
    return bare_instrument_track


@pytest.fixture
def default_instrument_track():
    return InstrumentTrack(
        _default_resolution,
        _default_instrument,
        _default_difficulty,
        _default_note_events,
        _default_star_power_events,
    )


@pytest.fixture
def bare_note_event():
    return NoteEvent.__new__(NoteEvent)


@pytest.fixture
def bare_note_event_parsed_data():
    return NoteEvent.ParsedData.__new__(NoteEvent.ParsedData)


@pytest.fixture
def default_note_event():
    return _default_note_event


@pytest.fixture
def bare_special_event():
    return SpecialEvent.__new__(SpecialEvent)


@pytest.fixture
def default_special_event():
    return SpecialEvent(_default_tick, _default_timestamp, _default_sustain)


@pytest.fixture
def bare_star_power_event():
    return StarPowerEvent.__new__(StarPowerEvent)


@pytest.fixture
def default_star_power_event():
    return _default_star_power_event


# sync.py object fixtures


@pytest.fixture
def bare_sync_track():
    return SyncTrack.__new__(SyncTrack)


@pytest.fixture
def minimal_sync_track(bare_sync_track):
    """Minimal initialization necessary to avoid attribute errors."""
    bare_sync_track.time_signature_events = []
    bare_sync_track.bpm_events = []
    return bare_sync_track


@pytest.fixture
def default_sync_track():
    return SyncTrack(
        _default_resolution,
        _default_time_signature_events,
        _default_bpm_events,
        _default_anchor_events,
    )


@pytest.fixture
def bare_time_signature_event():
    return TimeSignatureEvent.__new__(TimeSignatureEvent)


@pytest.fixture
def default_time_signature_event():
    return _default_time_signature_event


@pytest.fixture
def bare_bpm_event():
    return BPMEvent.__new__(BPMEvent)


@pytest.fixture
def default_bpm_event():
    return _default_bpm_event


# globalevents.py object fixtures


@pytest.fixture
def bare_global_events_track():
    return GlobalEventsTrack.__new__(GlobalEventsTrack)


@pytest.fixture
def minimal_global_events_track(bare_global_events_track):
    """Minimal initialization necessary to avoid attribute errors."""
    bare_global_events_track.text_events = []
    bare_global_events_track.section_events = []
    bare_global_events_track.lyric_events = []
    return bare_global_events_track


@pytest.fixture
def default_global_events_track():
    return GlobalEventsTrack(
        _default_resolution, _default_text_events, _default_section_events, _default_lyric_events
    )


@pytest.fixture
def bare_global_event():
    return GlobalEvent.__new__(GlobalEvent)


@pytest.fixture
def default_global_event():
    return _default_global_event


@pytest.fixture
def bare_text_event():
    return TextEvent.__new__(TextEvent)


@pytest.fixture
def default_text_event():
    return _default_text_event


@pytest.fixture
def bare_section_event():
    return SectionEvent.__new__(SectionEvent)


@pytest.fixture
def default_section_event():
    return _default_section_event


@pytest.fixture
def bare_lyric_event():
    return LyricEvent.__new__(LyricEvent)


@pytest.fixture
def default_lyric_event():
    return _default_lyric_event


# metadata.py object fixtures


@pytest.fixture
def bare_metadata():
    return Metadata.__new__(Metadata)


@pytest.fixture
def minimal_metadata():
    """Minimal initialization necessary to avoid attribute errors."""
    return Metadata(_default_resolution)


@pytest.fixture
def default_metadata():
    return Metadata(
        _default_resolution,
        _default_offset,
        _default_player2,
        _default_intensity,
        _default_preview_start,
        _default_preview_end,
        _default_genre,
        _default_media_type,
        _default_name,
        _default_artist,
        _default_charter,
        _default_album,
        _default_year,
        _default_music_stream,
        _default_guitar_stream,
        _default_rhythm_stream,
        _default_bass_stream,
        _default_drum_stream,
        _default_drum2_stream,
        _default_drum3_stream,
        _default_drum4_stream,
        _default_vocal_stream,
        _default_keys_stream,
        _default_crowd_stream,
    )
