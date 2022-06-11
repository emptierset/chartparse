import pytest

from chartparse.exceptions import RegexFatalNotMatchError
from chartparse.metadata import Metadata


class TestMetadata(object):
    fields = {
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

    def test_from_chart_lines(self):
        lines = [
            f"  Name = \"{self.fields['name']}\"",
            f"  Artist = \"{self.fields['artist']}\"",
            f"  Charter = \"{self.fields['charter']}\"",
            f"  Album = \"{self.fields['album']}\"",
            f"  Year = \"{self.fields['year']}\"",
            f"  Offset = {self.fields['offset']}",
            f"  Resolution = {self.fields['resolution']}",
            f"  Player2 = {self.fields['player2']}",
            f"  Difficulty = {self.fields['difficulty']}",
            f"  PreviewStart = {self.fields['preview_start']}",
            f"  PreviewEnd = {self.fields['preview_end']}",
            f"  Genre = \"{self.fields['genre']}\"",
            f"  MediaType = \"{self.fields['media_type']}\"",
            f"  MusicStream = \"{self.fields['music_stream']}\"",
            f"  UnknownProperty = \"{self.fields['unknown_property']}\"",
        ]
        metadata = Metadata.from_chart_lines(lines)
        assert metadata.name == self.fields["name"]
        assert metadata.artist == self.fields["artist"]
        assert metadata.charter == self.fields["charter"]
        assert metadata.album == self.fields["album"]
        assert metadata.year == self.fields["year"]
        assert metadata.offset == self.fields["offset"]
        assert metadata.resolution == self.fields["resolution"]
        assert metadata.player2 == self.fields["player2"]
        assert metadata.difficulty == self.fields["difficulty"]
        assert metadata.preview_start == self.fields["preview_start"]
        assert metadata.preview_end == self.fields["preview_end"]
        assert metadata.genre == self.fields["genre"]
        assert metadata.media_type == self.fields["media_type"]
        assert metadata.music_stream == self.fields["music_stream"]
        assert metadata.unknown_property == self.fields["unknown_property"]

    def test_from_chart_lines_no_match(self, invalid_chart_line):
        lines = [invalid_chart_line]
        with pytest.raises(RegexFatalNotMatchError):
            _ = Metadata.from_chart_lines(lines)

    def test_init(self):
        metadata = Metadata(self.fields)
        assert metadata.name == self.fields["name"]
        assert metadata.artist == self.fields["artist"]
        assert metadata.charter == self.fields["charter"]
        assert metadata.album == self.fields["album"]
        assert metadata.year == self.fields["year"]
        assert metadata.offset == self.fields["offset"]
        assert metadata.resolution == self.fields["resolution"]
        assert metadata.player2 == self.fields["player2"]
        assert metadata.difficulty == self.fields["difficulty"]
        assert metadata.preview_start == self.fields["preview_start"]
        assert metadata.preview_end == self.fields["preview_end"]
        assert metadata.genre == self.fields["genre"]
        assert metadata.media_type == self.fields["media_type"]
        assert metadata.music_stream == self.fields["music_stream"]
        assert metadata.unknown_property == self.fields["unknown_property"]
