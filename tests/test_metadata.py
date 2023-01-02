from __future__ import annotations

import pytest

from chartparse.exceptions import MissingRequiredField
from chartparse.metadata import Metadata


class TestMetadata(object):
    class TestFromChartLines(object):
        def test(self):
            lines = [
                f'  Name = "{pytest.defaults.name}"',
                f'  Artist = "{pytest.defaults.artist}"',
                f'  Charter = "{pytest.defaults.charter}"',
                f'  Album = "{pytest.defaults.album}"',
                f'  Year = "{pytest.defaults.year}"',
                f"  Offset = {pytest.defaults.offset_string}",
                f"  Resolution = {pytest.defaults.resolution_string}",
                f"  Player2 = {pytest.defaults.player2_string}",
                f"  Difficulty = {pytest.defaults.intensity_string}",
                f"  PreviewStart = {pytest.defaults.preview_start_string}",
                f"  PreviewEnd = {pytest.defaults.preview_end_string}",
                f'  Genre = "{pytest.defaults.genre}"',
                f'  MediaType = "{pytest.defaults.media_type}"',
                f'  MusicStream = "{pytest.defaults.music_stream}"',
                f'  GuitarStream = "{pytest.defaults.guitar_stream}"',
                f'  RhythmStream = "{pytest.defaults.rhythm_stream}"',
                f'  BassStream = "{pytest.defaults.bass_stream}"',
                f'  DrumStream = "{pytest.defaults.drum_stream}"',
                f'  Drum2Stream = "{pytest.defaults.drum2_stream}"',
                f'  Drum3Stream = "{pytest.defaults.drum3_stream}"',
                f'  Drum4Stream = "{pytest.defaults.drum4_stream}"',
                f'  VocalStream = "{pytest.defaults.vocal_stream}"',
                f'  KeysStream = "{pytest.defaults.keys_stream}"',
                f'  CrowdStream = "{pytest.defaults.crowd_stream}"',
            ]
            metadata = Metadata.from_chart_lines(lines)
            assert metadata.name == pytest.defaults.name
            assert metadata.artist == pytest.defaults.artist
            assert metadata.charter == pytest.defaults.charter
            assert metadata.album == pytest.defaults.album
            assert metadata.year == pytest.defaults.year
            assert metadata.offset == pytest.defaults.offset
            assert metadata.resolution == pytest.defaults.resolution
            assert metadata.player2 == pytest.defaults.player2
            assert metadata.difficulty == pytest.defaults.intensity
            assert metadata.preview_start == pytest.defaults.preview_start
            assert metadata.preview_end == pytest.defaults.preview_end
            assert metadata.genre == pytest.defaults.genre
            assert metadata.media_type == pytest.defaults.media_type
            assert metadata.music_stream == pytest.defaults.music_stream
            assert metadata.guitar_stream == pytest.defaults.guitar_stream
            assert metadata.rhythm_stream == pytest.defaults.rhythm_stream
            assert metadata.bass_stream == pytest.defaults.bass_stream
            assert metadata.drum_stream == pytest.defaults.drum_stream
            assert metadata.drum2_stream == pytest.defaults.drum2_stream
            assert metadata.drum3_stream == pytest.defaults.drum3_stream
            assert metadata.drum4_stream == pytest.defaults.drum4_stream
            assert metadata.vocal_stream == pytest.defaults.vocal_stream
            assert metadata.keys_stream == pytest.defaults.keys_stream
            assert metadata.crowd_stream == pytest.defaults.crowd_stream

        def test_missing_resolution(self):
            with pytest.raises(MissingRequiredField):
                _ = Metadata.from_chart_lines([])
