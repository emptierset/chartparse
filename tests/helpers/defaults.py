from __future__ import annotations

import datetime
import math

from chartparse.globalevents import (
    GlobalEvent,
    TextEvent,
    SectionEvent,
    LyricEvent,
)
from chartparse.instrument import (
    NoteEvent,
    NoteTrackIndex,
    TrackEvent,
    StarPowerEvent,
    Instrument,
    Difficulty,
    Note,
    HOPOState,
    _SustainList,
    SustainTuple,
)
from chartparse.metadata import Player2Instrument
from chartparse.sync import BPMEvent, TimeSignatureEvent, AnchorEvent


filepath = "/not/a/real/path"

tick = 0

timestamp = datetime.timedelta(0)

seconds = 0
microseconds = seconds // 1000000

proximal_bpm_event_index = 0
proximal_star_power_event_index = 0

bpm_events_timestamp = datetime.timedelta(seconds=111)
bpm_events_bpm_event_index = 222

bpm = 120.000
raw_bpm = str(int(bpm * 1000))
bpm_event = BPMEvent(tick=tick, timestamp=timestamp, bpm=bpm)
# TODO: Get rid of all "events" defaults and instead expect the user to wrap the individual default
# events in a list manually.
bpm_events = [bpm_event]
bpm_event_parsed_data = BPMEvent.ParsedData(tick=tick, raw_bpm=raw_bpm)
bpm_event_parsed_datas = [bpm_event_parsed_data]

upper_time_signature_numeral = 4
lower_time_signature_numeral = 8
raw_lower_time_signature_numeral = str(int(math.log(lower_time_signature_numeral, 2)))
time_signature_event = TimeSignatureEvent(
    tick=tick,
    timestamp=timestamp,
    upper_numeral=upper_time_signature_numeral,
    lower_numeral=lower_time_signature_numeral,
)
time_signature_events = [time_signature_event]
time_signature_event_parsed_data = TimeSignatureEvent.ParsedData(
    tick=tick,
    upper=upper_time_signature_numeral,
    lower=lower_time_signature_numeral,
)
time_signature_event_parsed_datas = [time_signature_event_parsed_data]

anchor_event = AnchorEvent(tick=tick, timestamp=timestamp)
anchor_events = [anchor_event]
anchor_event_parsed_data = AnchorEvent.ParsedData(tick=tick, microseconds=microseconds)
anchor_event_parsed_datas = [anchor_event_parsed_data]

global_event_value = "default_global_event_value"
global_event = GlobalEvent(tick=tick, timestamp=timestamp, value=global_event_value)
global_events = [global_event]
global_event_parsed_data = GlobalEvent.ParsedData(tick=tick, value=global_event_value)
global_event_parsed_datas = [global_event_parsed_data]

text_event_value = "default_text_event_value"
text_event = TextEvent(tick=tick, timestamp=timestamp, value=text_event_value)
text_events = [text_event]
text_event_parsed_data = TextEvent.ParsedData(tick=tick, value=text_event_value)
text_event_parsed_datas = [text_event_parsed_data]

section_event_value = "default_section_event_value"
section_event = SectionEvent(tick=tick, timestamp=timestamp, value=section_event_value)
section_events = [section_event]
section_event_parsed_data = SectionEvent.ParsedData(tick=tick, value=section_event_value)
section_event_parsed_datas = [section_event_parsed_data]

lyric_event_value = "default_lyric_event_value"
lyric_event = LyricEvent(tick=tick, timestamp=timestamp, value=lyric_event_value)
lyric_events = [lyric_event]
lyric_event_parsed_data = LyricEvent.ParsedData(tick=tick, value=lyric_event_value)
lyric_event_parsed_datas = [lyric_event_parsed_data]


difficulty = Difficulty.EXPERT
instrument = Instrument.GUITAR
section_name = difficulty.value + instrument.value
sustain = 0  # ticks
sustain_list = _SustainList([0, None, None, None, None])
sustain_tuple = SustainTuple((0, None, None, None, None))

note = Note.G
note_track_index = NoteTrackIndex.G

hopo_state = HOPOState.STRUM

note_event = NoteEvent(
    tick=tick,
    timestamp=timestamp,
    end_timestamp=timestamp,
    note=note,
    hopo_state=hopo_state,
)
note_events = [note_event]
note_event_parsed_data = NoteEvent.ParsedData(
    tick=tick,
    sustain=sustain,
    note_track_index=note_track_index,
)
note_event_parsed_datas = [note_event_parsed_data]

star_power_event = StarPowerEvent(tick=tick, timestamp=timestamp, sustain=sustain)
star_power_events = [star_power_event]
star_power_event_parsed_data = StarPowerEvent.ParsedData(tick=tick, sustain=sustain)
star_power_event_parsed_datas = [star_power_event_parsed_data]

track_event_value = "default_track_event_value"
track_event = TrackEvent(tick=tick, timestamp=timestamp, value=track_event_value)
track_events = [track_event]
track_event_parsed_data = TrackEvent.ParsedData(
    tick=tick,
    value=track_event_value,
)
track_event_parsed_datas = [track_event_parsed_data]

name = "Song Name"
artist = "Artist Name"
charter = "Charter Name"
album = "Album Name"
year = "1999"
offset = 0
offset_string = str(offset)
resolution = 192
resolution_string = str(resolution)
player2 = Player2Instrument.BASS
player2_string = player2.value
intensity = 2
intensity_string = str(intensity)
preview_start = 3
preview_start_string = str(preview_start)
preview_end = 4
preview_end_string = str(preview_end)
genre = "metal"
media_type = "vinyl"
music_stream = "song.ogg"
guitar_stream = "guitar.ogg"
rhythm_stream = "rhythm.ogg"
bass_stream = "bass.ogg"
drum_stream = "drum.ogg"
drum2_stream = "drum2.ogg"
drum3_stream = "drum3.ogg"
drum4_stream = "drum4.ogg"
vocal_stream = "vocal.ogg"
keys_stream = "keys.ogg"
crowd_stream = "crowd.ogg"

# https://stackoverflow.com/a/1845097
unmatchable_regex = r"(?!x)x"

invalid_chart_line = "this_line_is_invalid"
invalid_chart_lines = [invalid_chart_line]
