from __future__ import annotations

import math
from datetime import timedelta

from chartparse.globalevents import GlobalEvent, LyricEvent, SectionEvent, TextEvent
from chartparse.instrument import (
    Difficulty,
    HOPOState,
    Instrument,
    Note,
    NoteEvent,
    NoteTrackIndex,
    StarPowerEvent,
    SustainTuple,
    TrackEvent,
    _SustainList,
)
from chartparse.metadata import Player2Instrument
from chartparse.sync import AnchorEvent, BPMEvent, BPMEvents, TimeSignatureEvent
from chartparse.tick import Tick, Ticks
from chartparse.time import Timestamp

name = "Song Name"
artist = "Artist Name"
charter = "Charter Name"
album = "Album Name"
year = "1999"
offset = 0
offset_string = str(offset)
resolution = Ticks(192)
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

filepath = "/not/a/real/path"

tick = Tick(0)

timestamp = Timestamp(timedelta(0))

seconds = 0
microseconds = seconds // 1000000

proximal_bpm_event_index = 0
proximal_star_power_event_index = 0

timestamp_at_tick_timestamp = Timestamp(timedelta(seconds=111))
timestamp_at_tick_proximal_bpm_event_index = 222

bpm = 120.000
raw_bpm = str(int(bpm * 1000))
bpm_event = BPMEvent(tick=tick, timestamp=timestamp, bpm=bpm)
bpm_event_parsed_data = BPMEvent.ParsedData(tick=tick, raw_bpm=raw_bpm)

bpm_events = BPMEvents(events=[bpm_event], resolution=resolution)

upper_time_signature_numeral = 4
lower_time_signature_numeral = 8
raw_lower_time_signature_numeral = str(int(math.log(lower_time_signature_numeral, 2)))
time_signature_event = TimeSignatureEvent(
    tick=tick,
    timestamp=timestamp,
    upper_numeral=upper_time_signature_numeral,
    lower_numeral=lower_time_signature_numeral,
)
time_signature_event_parsed_data = TimeSignatureEvent.ParsedData(
    tick=tick,
    upper=upper_time_signature_numeral,
    lower=lower_time_signature_numeral,
)

anchor_event = AnchorEvent(tick=tick, timestamp=timestamp)
anchor_event_parsed_data = AnchorEvent.ParsedData(tick=tick, microseconds=microseconds)

global_event_value = "default_global_event_value"
global_event = GlobalEvent(tick=tick, timestamp=timestamp, value=global_event_value)
global_event_parsed_data = GlobalEvent.ParsedData(tick=tick, value=global_event_value)

text_event_value = "default_text_event_value"
text_event = TextEvent(tick=tick, timestamp=timestamp, value=text_event_value)
text_event_parsed_data = TextEvent.ParsedData(tick=tick, value=text_event_value)

section_event_value = "default_section_event_value"
section_event = SectionEvent(tick=tick, timestamp=timestamp, value=section_event_value)
section_event_parsed_data = SectionEvent.ParsedData(tick=tick, value=section_event_value)

lyric_event_value = "default_lyric_event_value"
lyric_event = LyricEvent(tick=tick, timestamp=timestamp, value=lyric_event_value)
lyric_event_parsed_data = LyricEvent.ParsedData(tick=tick, value=lyric_event_value)


difficulty = Difficulty.EXPERT
instrument = Instrument.GUITAR
header_tag = difficulty.value + instrument.value
sustain = Ticks(0)
sustain_list = _SustainList([Ticks(0), None, None, None, None])
sustain_tuple = SustainTuple((Ticks(0), None, None, None, None))

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
note_event_parsed_data = NoteEvent.ParsedData(
    tick=tick,
    sustain=sustain,
    note_track_index=note_track_index,
)

star_power_event = StarPowerEvent(tick=tick, timestamp=timestamp, sustain=sustain)
star_power_event_parsed_data = StarPowerEvent.ParsedData(tick=tick, sustain=sustain)

track_event_value = "default_track_event_value"
track_event = TrackEvent(tick=tick, timestamp=timestamp, value=track_event_value)
track_event_parsed_data = TrackEvent.ParsedData(
    tick=tick,
    value=track_event_value,
)

# https://stackoverflow.com/a/1845097
unmatchable_regex = r"(?!x)x"

invalid_chart_line = "this_line_is_invalid"
invalid_chart_lines = [invalid_chart_line]
