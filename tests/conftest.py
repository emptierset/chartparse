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
    StarPowerEvent,
    SpecialEvent,
    Instrument,
    Difficulty,
    Note,
)
from chartparse.metadata import Metadata, Player2Instrument
from chartparse.sync import SyncTrack, BPMEvent, TimeSignatureEvent

_invalid_chart_line = "this_line_is_invalid"

_default_filepath = "/not/a/real/path"

_default_tick = 0

_default_timestamp = datetime.timedelta(0)

_default_bpm = 120.000
_default_bpm_event = BPMEvent(_default_tick, _default_timestamp, _default_bpm)
_default_bpm_event_list = [_default_bpm_event]


# TODO: Put all line generation logic in some pytest_plugin module; see stackoverflow below:
# https://stackoverflow.com/questions/27064004/splitting-a-conftest-py-file-into-several-smaller-conftest-like-parts
@pytest.fixture
def generate_valid_bpm_line():
    return generate_valid_bpm_line_fn


@pytest.fixture
def valid_bpm_line_tick_1():
    return generate_valid_bpm_line_fn(tick=1)


def generate_valid_bpm_line_fn(tick=_default_tick, bpm=_default_bpm):
    bpm_sans_decimal_point = int(bpm * 1000)
    if bpm_sans_decimal_point != bpm * 1000:
        raise ValueError(f"bpm {bpm} has more than 3 decimal places")
    return f"  {tick} = B {bpm_sans_decimal_point}"


_default_upper_time_signature_numeral = 4
_default_lower_time_signature_numeral = 8
_default_time_signature_event = TimeSignatureEvent(
    _default_tick,
    _default_timestamp,
    _default_upper_time_signature_numeral,
    _default_lower_time_signature_numeral,
)
_default_time_signature_event_list = [_default_time_signature_event]


@pytest.fixture
def generate_valid_long_time_signature_line():
    def generate_valid_long_time_signature_line_fn():
        return generate_valid_time_signature_line_fn(
            lower_numeral=_default_lower_time_signature_numeral
        )

    return generate_valid_long_time_signature_line_fn


@pytest.fixture
def generate_valid_short_time_signature_line():
    return generate_valid_time_signature_line_fn


def generate_valid_time_signature_line_fn(
    tick=_default_tick, upper_numeral=_default_upper_time_signature_numeral, lower_numeral=None
):
    if lower_numeral:
        return f"  {tick} = TS {upper_numeral} {int(math.log(lower_numeral, 2))}"
    else:
        return f"  {tick} = TS {upper_numeral}"


_default_global_event_value = "default_global_event_value"
_default_text_event_value = "default_text_event_value"
_default_section_event_value = "default_section_event_value"
_default_lyric_event_value = "default_lyric_event_value"
_default_text_event = TextEvent(_default_tick, _default_text_event_value, _default_timestamp)
_default_section_event = SectionEvent(
    _default_tick, _default_section_event_value, _default_timestamp
)
_default_lyric_event = LyricEvent(_default_tick, _default_lyric_event_value, _default_timestamp)
# TODO: Rename all `events_list` and `event_list` names to `events`.
_default_text_events_list = [_default_text_event]
_default_section_events_list = [_default_section_event]
_default_lyric_events_list = [_default_lyric_event]


@pytest.fixture
def generate_valid_text_event_line():
    return generate_valid_text_event_line_fn


def generate_valid_text_event_line_fn(tick=_default_tick, value=_default_text_event_value):
    return f'  {tick} = E "{value}"'


@pytest.fixture
def generate_valid_section_event_line():
    return generate_valid_section_event_line_fn


def generate_valid_section_event_line_fn(tick=_default_tick, value=_default_section_event_value):
    return f'  {tick} = E "section {value}"'


@pytest.fixture
def generate_valid_lyric_event_line():
    return generate_valid_lyric_event_line_fn


def generate_valid_lyric_event_line_fn(tick=_default_tick, value=_default_lyric_event_value):
    return f'  {tick} = E "lyric {value}"'


_default_difficulty = Difficulty.EXPERT
_default_instrument = Instrument.GUITAR
_default_section_name = _default_difficulty.value + _default_instrument.value
_default_sustain = 0  # ticks

_default_note = Note.G
_default_note_instrument_track_index = InstrumentTrack._min_note_instrument_track_index


@pytest.fixture
def generate_valid_note_line():
    return generate_valid_note_line_fn


def generate_valid_note_line_fn(
    tick=_default_tick, note=_default_note_instrument_track_index, sustain=0
):
    return f"  {tick} = N {note} {sustain}"


_default_note_line = generate_valid_note_line_fn()
_default_note_event = NoteEvent(_default_tick, _default_timestamp, _default_note)
_default_note_event_list = [_default_note_event]


_default_star_power_event = StarPowerEvent(_default_tick, _default_timestamp, _default_sustain)
_default_star_power_event_list = [_default_star_power_event]

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


@pytest.fixture
def generate_valid_star_power_line():
    return generate_valid_star_power_line_fn


def generate_valid_star_power_line_fn(tick=_default_tick, sustain=_default_sustain):
    return f"  {tick} = S 2 {sustain}"


def dataclass_list_field(xs):
    return dataclasses.field(default_factory=lambda: list(xs))


@dataclasses.dataclass
class Defaults(object):
    filepath: ... = _default_filepath

    tick: ... = _default_tick
    sustain: ... = _default_sustain

    timestamp: ... = _default_timestamp

    name: ... = _default_name
    artist: ... = _default_artist
    charter: ... = _default_charter
    album: ... = _default_album
    year: ... = _default_year
    offset: ... = _default_offset
    offset_string: ... = _default_offset_string
    resolution: ... = _default_resolution
    resolution_string: ... = _default_resolution_string
    player2: ... = _default_player2
    player2_string: ... = _default_player2_string
    intensity: ... = _default_intensity
    intensity_string: ... = _default_intensity_string
    preview_start: ... = _default_preview_start
    preview_start_string: ... = _default_preview_start_string
    preview_end: ... = _default_preview_end
    preview_end_string: ... = _default_preview_end_string
    genre: ... = _default_genre
    media_type: ... = _default_media_type
    music_stream: ... = _default_music_stream
    guitar_stream: ... = _default_guitar_stream
    rhythm_stream: ... = _default_rhythm_stream
    bass_stream: ... = _default_bass_stream
    drum_stream: ... = _default_drum_stream
    drum2_stream: ... = _default_drum2_stream
    drum3_stream: ... = _default_drum3_stream
    drum4_stream: ... = _default_drum4_stream
    vocal_stream: ... = _default_vocal_stream
    keys_stream: ... = _default_keys_stream
    crowd_stream: ... = _default_crowd_stream

    bpm: ... = _default_bpm
    bpm_event: ... = _default_bpm_event
    bpm_event_list: ... = dataclass_list_field(_default_bpm_event_list)

    upper_time_signature_numeral: ... = _default_upper_time_signature_numeral
    lower_time_signature_numeral: ... = _default_lower_time_signature_numeral
    time_signature_event: ... = _default_time_signature_event
    time_signature_event_list: ... = dataclass_list_field(_default_time_signature_event_list)

    global_event_value: ... = _default_global_event_value
    text_event_value: ... = _default_text_event_value
    section_event_value: ... = _default_section_event_value
    lyric_event_value: ... = _default_lyric_event_value
    text_event: ... = _default_text_event
    section_event: ... = _default_section_event
    lyric_event: ... = _default_lyric_event
    text_event_list: ... = dataclass_list_field(_default_text_events_list)
    section_event_list: ... = dataclass_list_field(_default_section_events_list)
    lyric_event_list: ... = dataclass_list_field(_default_lyric_events_list)

    instrument: ... = _default_instrument
    difficulty: ... = _default_difficulty
    section_name: ... = _default_section_name

    note: ... = _default_note
    note_event: ... = _default_note_event
    note_event_list: ... = dataclass_list_field(_default_note_event_list)

    star_power_event: ... = _default_star_power_event
    star_power_event_list: ... = dataclass_list_field(_default_star_power_event_list)


def pytest_configure():
    pytest.invalid_chart_line = _invalid_chart_line
    pytest.unmatchable_regex = _unmatchable_regex
    pytest.defaults = Defaults()


@pytest.fixture
def mock_open_empty_string(mocker):
    mocker.patch("builtins.open", mocker.mock_open(read_data=""))


@pytest.fixture
def invalid_chart_line():
    return _invalid_chart_line


@pytest.fixture
def minimal_timestamp_getter():
    def f(resolution, tick, start_bpm_event_index=0):
        return (datetime.timedelta(0), 0)

    return f


@pytest.fixture
def minimal_string_iterator_getter(invalid_chart_line):
    return lambda: [invalid_chart_line]


@pytest.fixture
def unmatchable_regex():
    return _unmatchable_regex


@pytest.fixture
def default_event():
    return Event(_default_tick, _default_timestamp)


@pytest.fixture
def bare_note_event():
    return NoteEvent.__new__(NoteEvent)


# TODO: Reorder fixtures sensibly.
@pytest.fixture
def bare_special_event():
    return SpecialEvent.__new__(SpecialEvent)


@pytest.fixture
def default_time_signature_event():
    return _default_time_signature_event


@pytest.fixture
def default_bpm_event():
    return _default_bpm_event


@pytest.fixture
def bare_global_event():
    return GlobalEvent.__new__(GlobalEvent)


@pytest.fixture
def default_text_event():
    return _default_text_event


@pytest.fixture
def default_section_event():
    return _default_section_event


@pytest.fixture
def default_lyric_event():
    return _default_lyric_event


@pytest.fixture
def default_note_event():
    return _default_note_event


@pytest.fixture
def default_star_power_event():
    return _default_star_power_event


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
def tick_having_event(request):
    return request.getfixturevalue(request.param)


@pytest.fixture
def note_lines():
    return [_default_note_line]


@pytest.fixture
def bare_metadata():
    return Metadata.__new__(Metadata)


@pytest.fixture
def minimal_metadata():
    return Metadata(_default_resolution)


@pytest.fixture
def basic_metadata():
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


@pytest.fixture
def bare_global_events_track():
    return GlobalEventsTrack.__new__(GlobalEventsTrack)


@pytest.fixture
def minimal_global_events_track(bare_global_events_track):
    bare_global_events_track.text_events = []
    bare_global_events_track.section_events = []
    bare_global_events_track.lyric_events = []
    return bare_global_events_track


@pytest.fixture
def basic_global_events_track():
    return GlobalEventsTrack(
        _default_text_events_list, _default_section_events_list, _default_lyric_events_list
    )


@pytest.fixture
def bare_sync_track():
    return SyncTrack.__new__(SyncTrack)


@pytest.fixture
def minimal_sync_track(bare_sync_track):
    bare_sync_track.time_signature_events = []
    bare_sync_track.bpm_events = []
    return bare_sync_track


@pytest.fixture
def basic_sync_track():
    return SyncTrack(_default_time_signature_event_list, _default_bpm_event_list)


@pytest.fixture
def bare_instrument_track():
    return InstrumentTrack.__new__(InstrumentTrack)


@pytest.fixture
def minimal_instrument_track(bare_instrument_track):
    bare_instrument_track.instrument = _default_instrument
    bare_instrument_track.difficulty = _default_difficulty
    bare_instrument_track.section_name = "ExpertSingle"
    bare_instrument_track.note_events = []
    bare_instrument_track.star_power_events = []
    return bare_instrument_track


@pytest.fixture
def basic_instrument_track():
    return InstrumentTrack(
        _default_instrument,
        _default_difficulty,
        _default_note_event_list,
        _default_star_power_event_list,
    )


@pytest.fixture
def basic_instrument_tracks(basic_instrument_track):
    return {_default_instrument: {_default_difficulty: basic_instrument_track}}


@pytest.fixture
def bare_chart():
    return Chart.__new__(Chart)


@pytest.fixture
def minimal_chart(
    bare_chart,
    minimal_metadata,
    minimal_instrument_track,
    minimal_sync_track,
    minimal_global_events_track,
):
    bare_chart.metadata = minimal_metadata
    bare_chart.sync_track = minimal_sync_track
    bare_chart.global_events_track = minimal_global_events_track
    bare_chart.instrument_tracks = {
        _default_instrument: {
            _default_difficulty: minimal_instrument_track,
        }
    }
    return bare_chart


@pytest.fixture
def basic_chart(
    basic_metadata,
    basic_global_events_track,
    basic_sync_track,
    basic_instrument_track,
):
    basic_instrument_tracks_dict = {
        _default_instrument: {_default_difficulty: basic_instrument_track}
    }
    return Chart(
        basic_metadata, basic_global_events_track, basic_sync_track, basic_instrument_tracks_dict
    )
