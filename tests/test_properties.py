import pytest

from chartparse.exceptions import RegexFatalNotMatchError
from chartparse.properties import Properties


class TestProperties(object):
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
        properties = Properties.from_chart_lines(lines)
        assert properties.name == self.fields["name"]
        assert properties.artist == self.fields["artist"]
        assert properties.charter == self.fields["charter"]
        assert properties.album == self.fields["album"]
        assert properties.year == self.fields["year"]
        assert properties.offset == self.fields["offset"]
        assert properties.resolution == self.fields["resolution"]
        assert properties.player2 == self.fields["player2"]
        assert properties.difficulty == self.fields["difficulty"]
        assert properties.preview_start == self.fields["preview_start"]
        assert properties.preview_end == self.fields["preview_end"]
        assert properties.genre == self.fields["genre"]
        assert properties.media_type == self.fields["media_type"]
        assert properties.music_stream == self.fields["music_stream"]
        assert properties.unknown_property == self.fields["unknown_property"]

    def test_from_chart_lines_no_match(self, invalid_chart_line):
        lines = [invalid_chart_line]
        with pytest.raises(RegexFatalNotMatchError):
            _ = Properties.from_chart_lines(lines)

    def test_init(self):
        properties = Properties(self.fields)
        assert properties.name == self.fields["name"]
        assert properties.artist == self.fields["artist"]
        assert properties.charter == self.fields["charter"]
        assert properties.album == self.fields["album"]
        assert properties.year == self.fields["year"]
        assert properties.offset == self.fields["offset"]
        assert properties.resolution == self.fields["resolution"]
        assert properties.player2 == self.fields["player2"]
        assert properties.difficulty == self.fields["difficulty"]
        assert properties.preview_start == self.fields["preview_start"]
        assert properties.preview_end == self.fields["preview_end"]
        assert properties.genre == self.fields["genre"]
        assert properties.media_type == self.fields["media_type"]
        assert properties.music_stream == self.fields["music_stream"]
        assert properties.unknown_property == self.fields["unknown_property"]
