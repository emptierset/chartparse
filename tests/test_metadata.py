from __future__ import annotations

import pytest

from chartparse.exceptions import MissingRequiredField
from chartparse.metadata import Metadata
from tests.helpers import defaults


class TestMetadata(object):
    class TestFromChartLines(object):
        def test(self) -> None:
            lines = [
                f'  Name = "{defaults.name}"',
                f'  Artist = "{defaults.artist}"',
                f'  Charter = "{defaults.charter}"',
                f'  Album = "{defaults.album}"',
                f'  Year = "{defaults.year}"',
                f"  Offset = {defaults.offset_string}",
                f"  Resolution = {defaults.resolution_string}",
                f"  Player2 = {defaults.player2_string}",
                f"  Difficulty = {defaults.intensity_string}",
                f"  PreviewStart = {defaults.preview_start_string}",
                f"  PreviewEnd = {defaults.preview_end_string}",
                f'  Genre = "{defaults.genre}"',
                f'  MediaType = "{defaults.media_type}"',
                f'  MusicStream = "{defaults.music_stream}"',
                f'  GuitarStream = "{defaults.guitar_stream}"',
                f'  RhythmStream = "{defaults.rhythm_stream}"',
                f'  BassStream = "{defaults.bass_stream}"',
                f'  DrumStream = "{defaults.drum_stream}"',
                f'  Drum2Stream = "{defaults.drum2_stream}"',
                f'  Drum3Stream = "{defaults.drum3_stream}"',
                f'  Drum4Stream = "{defaults.drum4_stream}"',
                f'  VocalStream = "{defaults.vocal_stream}"',
                f'  KeysStream = "{defaults.keys_stream}"',
                f'  CrowdStream = "{defaults.crowd_stream}"',
            ]
            metadata = Metadata.from_chart_lines(lines)
            assert metadata.name == defaults.name
            assert metadata.artist == defaults.artist
            assert metadata.charter == defaults.charter
            assert metadata.album == defaults.album
            assert metadata.year == defaults.year
            assert metadata.offset == defaults.offset
            assert metadata.resolution == defaults.resolution
            assert metadata.player2 == defaults.player2
            assert metadata.difficulty == defaults.intensity
            assert metadata.preview_start == defaults.preview_start
            assert metadata.preview_end == defaults.preview_end
            assert metadata.genre == defaults.genre
            assert metadata.media_type == defaults.media_type
            assert metadata.music_stream == defaults.music_stream
            assert metadata.guitar_stream == defaults.guitar_stream
            assert metadata.rhythm_stream == defaults.rhythm_stream
            assert metadata.bass_stream == defaults.bass_stream
            assert metadata.drum_stream == defaults.drum_stream
            assert metadata.drum2_stream == defaults.drum2_stream
            assert metadata.drum3_stream == defaults.drum3_stream
            assert metadata.drum4_stream == defaults.drum4_stream
            assert metadata.vocal_stream == defaults.vocal_stream
            assert metadata.keys_stream == defaults.keys_stream
            assert metadata.crowd_stream == defaults.crowd_stream

        def test_missing_resolution(self) -> None:
            with pytest.raises(MissingRequiredField):
                _ = Metadata.from_chart_lines([])
