import math
import pytest

from chartparse.chart import Chart
from chartparse.enums import Instrument, Difficulty, Note
from chartparse.event import Event
from chartparse.globalevents import (
    GlobalEventsTrack,
    TextEvent,
    SectionEvent,
    LyricEvent,
)
from chartparse.instrument import InstrumentTrack, NoteEvent, StarPowerEvent
from chartparse.metadata import Metadata
from chartparse.sync import SyncTrack, BPMEvent, TimeSignatureEvent
from chartparse.track import EventTrack

_invalid_chart_line = "this_line_is_invalid"

_default_filepath = "/not/a/real/path"

_default_tick = 0

_default_bpm = 120.000
_default_bpm_event = BPMEvent(_default_tick, _default_bpm)
_default_bpm_event_list = [_default_bpm_event]


# TODO: Put all line generation logic in some pytest_plugin module; see stackoverflow below:
# https://stackoverflow.com/questions/27064004/splitting-a-conftest-py-file-into-several-smaller-conftest-like-parts
@pytest.fixture
def generate_valid_bpm_line():
    return generate_valid_bpm_line_fn


def generate_valid_bpm_line_fn(tick=_default_tick, bpm=_default_bpm):
    bpm_sans_decimal_point = int(bpm * 1000)
    if bpm_sans_decimal_point != bpm * 1000:
        raise ValueError(f"bpm {bpm} has more than 3 decimal places")
    return f"  {tick} = B {bpm_sans_decimal_point}"


_default_upper_time_signature_numeral = 4
_default_lower_time_signature_numeral = 8
_default_time_signature_event = TimeSignatureEvent(
    _default_tick, _default_upper_time_signature_numeral, _default_lower_time_signature_numeral
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
_default_text_event = TextEvent(_default_tick, _default_text_event_value)
_default_section_event = SectionEvent(_default_tick, _default_section_event_value)
_default_lyric_event = LyricEvent(_default_tick, _default_lyric_event_value)
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
_default_sustain = 100  # ticks

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
_default_note_event = NoteEvent(_default_tick, _default_note)
_default_note_event_list = [_default_note_event]


_default_star_power_event = StarPowerEvent(_default_tick, _default_sustain)
_default_star_power_event_list = [_default_star_power_event]

_default_metadata_fields = {
    "name": "Song Name",
    "artist": "Artist Name",
    "charter": "Charter Name",
    "album": "Album Name",
    "year": "1999",
    "offset": 0,
    "resolution": 1,
    "player2": "bass",
    "difficulty": 2,
    "preview_start": 3,
    "preview_end": 4,
    "genre": "rock",
    "media_type": "cd",
    "music_stream": "song.ogg",
    "unknown_property": "unknown value",
}


@pytest.fixture
def generate_valid_star_power_line():
    return generate_valid_star_power_line_fn


def generate_valid_star_power_line_fn(tick=_default_tick, sustain=_default_sustain):
    return f"  {tick} = S 2 {sustain}"


def pytest_configure():
    pytest.invalid_chart_line = _invalid_chart_line

    pytest.default_filepath = _default_filepath

    pytest.default_tick = _default_tick
    pytest.default_sustain = _default_sustain

    pytest.default_bpm = _default_bpm
    pytest.default_bpm_event = _default_bpm_event
    pytest.default_bpm_event_list = _default_bpm_event_list

    pytest.default_upper_time_signature_numeral = _default_upper_time_signature_numeral
    pytest.default_lower_time_signature_numeral = _default_lower_time_signature_numeral
    pytest.default_time_signature_event_list = _default_time_signature_event_list

    pytest.default_global_event_value = _default_global_event_value
    pytest.default_text_event_value = _default_text_event_value
    pytest.default_section_event_value = _default_section_event_value
    pytest.default_lyric_event_value = _default_lyric_event_value
    pytest.default_text_event_list = _default_text_events_list
    pytest.default_section_event_list = _default_section_events_list
    pytest.default_lyric_event_list = _default_lyric_events_list

    pytest.default_instrument = _default_instrument
    pytest.default_difficulty = _default_difficulty

    pytest.default_note = _default_note
    pytest.default_note_event_list = _default_note_event_list

    pytest.default_star_power_event_list = _default_star_power_event_list


@pytest.fixture
def mock_open_empty_string(mocker):
    mocker.patch("builtins.open", mocker.mock_open(read_data=""))


@pytest.fixture
def invalid_chart_line():
    return _invalid_chart_line


@pytest.fixture
def placeholder_string_iterator_getter(invalid_chart_line):
    return lambda: [invalid_chart_line]


@pytest.fixture
def unmatchable_regex():
    # https://stackoverflow.com/a/1845097
    return r"(?!x)x"


# TODO: Rename to `event`.
@pytest.fixture
def tick_event():
    return Event(_default_tick)


@pytest.fixture
def time_signature_event():
    return _default_time_signature_event


@pytest.fixture
def bpm_event():
    return _default_bpm_event


@pytest.fixture
def text_event():
    return _default_text_event


@pytest.fixture
def section_event():
    return _default_section_event


@pytest.fixture
def lyric_event():
    return _default_lyric_event


# TODO: ... why does coverage care about this fixture?
@pytest.fixture
def note_event():  # pragma: no cover
    return _default_note_event


@pytest.fixture
def note_event_with_all_optionals_set():
    return NoteEvent(
        _default_tick, _default_note, sustain=_default_sustain, is_forced=True, is_tap=True
    )


@pytest.fixture
def star_power_event():
    return _default_star_power_event


@pytest.fixture(
    params=[
        "tick_event",
        "time_signature_event",
        "bpm_event",
        "text_event",
        "section_event",
        "lyric_event",
        "note_event",
        "star_power_event",
    ]
)
def tick_having_event(request):
    return request.getfixturevalue(request.param)


# TODO: ... why does coverage care about this fixture?
@pytest.fixture
def note_lines():  # pragma: no cover
    return [_default_note_line]


@pytest.fixture
def basic_metadata():
    return Metadata(_default_metadata_fields)


@pytest.fixture
def bare_event_track():
    return EventTrack.__new__(EventTrack)


@pytest.fixture
def basic_global_events_track(mocker, placeholder_string_iterator_getter):
    mocker.patch(
        "chartparse.globalevents.GlobalEventsTrack._parse_events_from_iterable",
        side_effect=[
            _default_text_events_list,
            _default_section_events_list,
            _default_lyric_events_list,
        ],
    )
    return GlobalEventsTrack(placeholder_string_iterator_getter)


@pytest.fixture
def bare_sync_track():
    return SyncTrack.__new__(SyncTrack)


@pytest.fixture
def basic_sync_track(mocker, placeholder_string_iterator_getter):
    mocker.patch(
        "chartparse.sync.SyncTrack._parse_events_from_iterable",
        side_effect=[_default_time_signature_event_list, _default_bpm_event_list],
    )
    return SyncTrack(placeholder_string_iterator_getter)


@pytest.fixture
def bare_instrument_track():
    return InstrumentTrack.__new__(InstrumentTrack)


@pytest.fixture
def basic_instrument_track(mocker, placeholder_string_iterator_getter):
    mocker.patch(
        "chartparse.instrument.InstrumentTrack._parse_note_events_from_iterable",
        return_value=_default_note_event_list,
    )
    mocker.patch(
        "chartparse.instrument.InstrumentTrack._parse_events_from_iterable",
        return_value=_default_star_power_event_list,
    )
    return InstrumentTrack(
        pytest.default_instrument, pytest.default_difficulty, placeholder_string_iterator_getter
    )


@pytest.fixture
def basic_chart(
    mocker,
    mock_open_empty_string,
    placeholder_string_iterator_getter,
    basic_metadata,
    basic_sync_track,
    basic_instrument_track,
):
    def fake_sync_track_init(self, iterator_getter):
        self.time_signature_events = _default_time_signature_event_list
        self.bpm_events = _default_bpm_event_list

    mocker.patch.object(SyncTrack, "__init__", fake_sync_track_init)

    def fake_global_events_track_init(self, iterator_getter):
        self.text_events = _default_text_events_list
        self.section_events = _default_section_events_list
        self.lyric_events = _default_lyric_events_list

    mocker.patch.object(GlobalEventsTrack, "__init__", fake_global_events_track_init)

    def fake_instrument_track_init(self, instrument, difficulty, iterator_getter):
        self.instrument = _default_instrument
        self.difficulty = _default_difficulty
        self.note_events = _default_note_event_list
        self.star_power_events = _default_star_power_event_list

    mocker.patch.object(InstrumentTrack, "__init__", fake_instrument_track_init)

    mocker.patch(
        "chartparse.chart.Chart._find_sections",
        return_value={
            "Song": placeholder_string_iterator_getter,
            "Events": placeholder_string_iterator_getter,
            "SyncTrack": placeholder_string_iterator_getter,
            "ExpertSingle": placeholder_string_iterator_getter,
        },
    )
    mocker.patch("chartparse.metadata.Metadata.from_chart_lines", return_value=basic_metadata)
    with open(_default_filepath, "r") as f:
        return Chart(f)
