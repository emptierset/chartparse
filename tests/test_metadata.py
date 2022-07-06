import pytest

from chartparse.exceptions import MissingRequiredField
from chartparse.metadata import Metadata


class TestMetadata(object):
    def test_init(self, basic_metadata):
        assert basic_metadata.name == pytest.default_name
        assert basic_metadata.artist == pytest.default_artist
        assert basic_metadata.charter == pytest.default_charter
        assert basic_metadata.album == pytest.default_album
        assert basic_metadata.year == pytest.default_year
        assert basic_metadata.offset == pytest.default_offset
        assert basic_metadata.resolution == pytest.default_resolution
        assert basic_metadata.player2 == pytest.default_player2
        assert basic_metadata.difficulty == pytest.default_intensity
        assert basic_metadata.preview_start == pytest.default_preview_start
        assert basic_metadata.preview_end == pytest.default_preview_end
        assert basic_metadata.genre == pytest.default_genre
        assert basic_metadata.media_type == pytest.default_media_type
        assert basic_metadata.music_stream == pytest.default_music_stream

    def test_from_chart_lines(self):
        lines = [
            f'  Name = "{pytest.default_name}"',
            f'  Artist = "{pytest.default_artist}"',
            f'  Charter = "{pytest.default_charter}"',
            f'  Album = "{pytest.default_album}"',
            f'  Year = "{pytest.default_year}"',
            f"  Offset = {pytest.default_offset_string}",
            f"  Resolution = {pytest.default_resolution_string}",
            f"  Player2 = {pytest.default_player2_string}",
            f"  Difficulty = {pytest.default_intensity_string}",
            f"  PreviewStart = {pytest.default_preview_start_string}",
            f"  PreviewEnd = {pytest.default_preview_end_string}",
            f'  Genre = "{pytest.default_genre}"',
            f'  MediaType = "{pytest.default_media_type}"',
            f'  MusicStream = "{pytest.default_music_stream}"',
        ]
        metadata = Metadata.from_chart_lines(lambda: iter(lines))
        assert metadata.name == pytest.default_name
        assert metadata.artist == pytest.default_artist
        assert metadata.charter == pytest.default_charter
        assert metadata.album == pytest.default_album
        assert metadata.year == pytest.default_year
        assert metadata.offset == pytest.default_offset
        assert metadata.resolution == pytest.default_resolution
        assert metadata.player2 == pytest.default_player2
        assert metadata.difficulty == pytest.default_intensity
        assert metadata.preview_start == pytest.default_preview_start
        assert metadata.preview_end == pytest.default_preview_end
        assert metadata.genre == pytest.default_genre
        assert metadata.media_type == pytest.default_media_type
        assert metadata.music_stream == pytest.default_music_stream

    def test_from_chart_lines_missing_resolution(self):
        with pytest.raises(MissingRequiredField):
            _ = Metadata.from_chart_lines(lambda: iter([]))
