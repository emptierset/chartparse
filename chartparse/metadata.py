from __future__ import annotations

import dataclasses
import enum
import re
from collections.abc import Callable, Iterable
from typing import Literal, Optional, Pattern, Type, TypedDict, TypeVar, Union

from chartparse.exceptions import MissingRequiredField, RegexNotMatchError, raise_
from chartparse.track import HasSectionNameMixin
from chartparse.util import DictPropertiesEqMixin, DictReprMixin

SnakeCaseFieldNameT = Literal[
    "resolution",
    "offset",
    "player2",
    "difficulty",
    "preview_start",
    "preview_end",
    "genre",
    "media_type",
    "name",
    "artist",
    "charter",
    "album",
    "year",
    "music_stream",
]

PascalCaseFieldNameT = Literal[
    "Resolution",
    "Offset",
    "Player2",
    "Difficulty",
    "PreviewStart",
    "PreviewEnd",
    "Genre",
    "MediaType",
    "Name",
    "Artist",
    "Charter",
    "Album",
    "Year",
    "MusicStream",
]

FieldValueT = Union[int, str, "Player2Instrument"]


class Player2Instrument(enum.Enum):
    """The instrument type of the co-op guitar chart in Guitar Hero 3."""

    BASS = "bass"
    RHYTHM = "rhythm"


def _make_field_regex(
    field_name: PascalCaseFieldNameT, value_regex: str, is_value_quoted: bool
) -> str:
    to_join = [rf"^\s*?{field_name} = "]
    if is_value_quoted:
        to_join.append(r'"')
    to_join.append(rf"({value_regex})")
    if is_value_quoted:
        to_join.append(r'"')
    to_join.append(r"\s*?$")
    return "".join(to_join)


def _make_int_field_regex(field_name: PascalCaseFieldNameT) -> str:
    return _make_field_regex(field_name, r"\d+?", False)


def _make_multiword_str_field_regex(field_name: PascalCaseFieldNameT) -> str:
    return _make_field_regex(field_name, r".+?", True)


def _make_quoteless_str_field_regex(field_name: PascalCaseFieldNameT) -> str:
    return _make_field_regex(field_name, r'[^"]+?', False)


class _FieldValuesDict(TypedDict, total=False):
    resolution: int
    offset: int
    player2: Player2Instrument
    difficulty: int
    preview_start: int
    preview_end: int
    genre: str
    media_type: str
    name: str
    artist: str
    charter: str
    album: str
    year: str
    music_stream: str


@dataclasses.dataclass
class _FieldParsingSpec(object):
    """A bundle of data necessary to parse a field from a ``.chart`` file.

    This is a dataclass because it allows us to evade this mypy bug:
    https://github.com/python/mypy/issues/708
    """

    regex: str
    regex_prog: Pattern[str] = dataclasses.field(init=False)
    processing_fn: Callable[[str], FieldValueT]

    def __post_init__(self) -> None:
        self.regex_prog = re.compile(self.regex)


class _FieldParsingSpecDict(TypedDict):
    resolution: _FieldParsingSpec
    offset: _FieldParsingSpec
    player2: _FieldParsingSpec
    difficulty: _FieldParsingSpec
    preview_start: _FieldParsingSpec
    preview_end: _FieldParsingSpec
    genre: _FieldParsingSpec
    media_type: _FieldParsingSpec
    name: _FieldParsingSpec
    artist: _FieldParsingSpec
    charter: _FieldParsingSpec
    album: _FieldParsingSpec
    year: _FieldParsingSpec
    music_stream: _FieldParsingSpec


_field_parsing_specs: _FieldParsingSpecDict = {
    "resolution": _FieldParsingSpec(
        _make_int_field_regex("Resolution"),
        int,
    ),
    "offset": _FieldParsingSpec(
        _make_int_field_regex("Offset"),
        int,
    ),
    "player2": _FieldParsingSpec(
        _make_quoteless_str_field_regex("Player2"), lambda s: Player2Instrument(s)
    ),
    "difficulty": _FieldParsingSpec(
        _make_int_field_regex("Difficulty"),
        int,
    ),
    "preview_start": _FieldParsingSpec(
        _make_int_field_regex("PreviewStart"),
        int,
    ),
    "preview_end": _FieldParsingSpec(
        _make_int_field_regex("PreviewEnd"),
        int,
    ),
    "genre": _FieldParsingSpec(
        _make_multiword_str_field_regex("Genre"),
        str,
    ),
    "media_type": _FieldParsingSpec(
        _make_multiword_str_field_regex("MediaType"),
        str,
    ),
    "name": _FieldParsingSpec(
        _make_multiword_str_field_regex("Name"),
        str,
    ),
    "artist": _FieldParsingSpec(
        _make_multiword_str_field_regex("Artist"),
        str,
    ),
    "charter": _FieldParsingSpec(
        _make_multiword_str_field_regex("Charter"),
        str,
    ),
    "album": _FieldParsingSpec(
        _make_multiword_str_field_regex("Album"),
        str,
    ),
    "year": _FieldParsingSpec(
        _make_multiword_str_field_regex("Year"),
        str,
    ),
    "music_stream": _FieldParsingSpec(
        _make_multiword_str_field_regex("MusicStream"),
        str,
    ),
}

MetadataT = TypeVar("MetadataT", bound="Metadata")


# TODO: Parse multiple audiostreams; Audio streams can include:
#     MusicStream = "5000 Robots.ogg"
#     GuitarStream = "guitar.ogg"
#     RhythmStream = "rhythm.ogg"
#     BassStream = "bass.ogg"
#     DrumStream = "drums_1.ogg"
#     Drum2Stream = "drums_2.ogg"
#     Drum3Stream = "drums_3.ogg"
#     Drum4Stream = "drums_4.ogg"
#     VocalStream = “vocals.ogg”
#     KeysStream = “keys.ogg”
#     CrowdStream = “crowd.ogg”
class Metadata(HasSectionNameMixin, DictPropertiesEqMixin, DictReprMixin):
    """All of a :class:`~chartparse.chart.Chart` object's metadata."""

    section_name = "Song"

    resolution: int
    """The number of ticks for which a quarter note lasts."""

    offset: int
    """The number of seconds in time before tick 0 is reached.

    This is a legacy field and should most likely be ignored.
    """

    player2: Player2Instrument
    """The instrument type of the co-op guitar chart in Guitar Hero 3."""

    difficulty: int
    """The perceived difficulty to play the chart.

    This is often referred to as "intensity".
    """

    preview_start: int
    """The number of seconds into the song at which the song preview should start.

    Might not actually be seconds. Typically, ``preview_start_time`` in ``song.ini`` is respected
    for Clone Hero instead.
    """

    preview_end: int
    """The number of seconds into the song at which the song preview should end.

    Might not actually be seconds. Clone Hero just plays a preview of a particular length starting
    at ``preview_start_time`` in ``song.ini``, so this is unlikely to ever do anything in modern
    Guitar Hero.
    """

    genre: str
    """The genre of the chart's song."""

    media_type: str
    """The type of media from which the chart's song originates."""

    name: str
    """The name of the chart's song."""

    artist: str
    """The name of the chart's song's artist."""

    charter: str
    """The user who made this chart."""

    album: str
    """The name of the chart's song's album."""

    year: str
    """The year the chart's song came out.

    This is formatted as, e.g. ", 2018" because it saved time when importing into GHTCP (Guitar
    Hero Three Control Panel).
    """

    music_stream: str
    """The filename of the main music track."""

    def __init__(
        self,
        resolution: int,
        offset: int = 0,
        player2: Player2Instrument = Player2Instrument.BASS,
        difficulty: int = 0,
        preview_start: int = 0,
        preview_end: int = 0,
        genre: str = "rock",
        media_type: str = "cd",
        name: Optional[str] = None,
        artist: Optional[str] = None,
        charter: Optional[str] = None,
        album: Optional[str] = None,
        year: Optional[str] = None,
        music_stream: Optional[str] = None,
    ) -> None:
        """Initializes all instance attributes."""

        self.resolution = resolution
        self.offset = offset
        self.player2 = player2
        self.difficulty = difficulty
        self.preview_start = preview_start
        self.preview_end = preview_end
        self.genre = genre
        self.media_type = media_type
        if name is not None:
            self.name = name
        if artist is not None:
            self.artist = artist
        if charter is not None:
            self.charter = charter
        if album is not None:
            self.album = album
        if year is not None:
            self.year = year
        if music_stream is not None:
            self.music_stream = music_stream

    @classmethod
    def from_chart_lines(
        cls: Type[MetadataT], iterator_getter: Callable[[], Iterable[str]]
    ) -> MetadataT:
        """Initializes instance attributes by parsing an iterable of strings.

        Args:
            iterator_getter: The iterable of strings returned by this is most likely from a
                Moonscraper ``.chart``. Must be a function so the strings can be iterated over
                multiple times, if necessary.
        """
        kwargs: _FieldValuesDict = dict()

        def set_kwarg(
            field_name: SnakeCaseFieldNameT,
            regex_not_match_callback: Optional[Callable[[], None]] = None,
        ) -> None:
            maybe_set_kwarg(
                field_name,
                regex_not_match_callback=lambda: raise_(MissingRequiredField(field_name)),
            )

        def maybe_set_kwarg(
            field_name: SnakeCaseFieldNameT,
            regex_not_match_callback: Optional[Callable[[], None]] = None,
        ) -> None:
            try:
                kwargs[field_name] = parse_all_lines_for_field(field_name)
            except RegexNotMatchError:
                if regex_not_match_callback is not None:
                    regex_not_match_callback()

        def parse_all_lines_for_field(field_name: SnakeCaseFieldNameT) -> FieldValueT:
            regex_prog = _field_parsing_specs[field_name].regex_prog
            for line in iterator_getter():
                m = regex_prog.match(line)
                if m:
                    return _field_parsing_specs[field_name].processing_fn(m.group(1))
            raise RegexNotMatchError(_field_parsing_specs[field_name].regex)

        set_kwarg("resolution")
        maybe_set_kwarg("offset")
        maybe_set_kwarg("player2")
        maybe_set_kwarg("difficulty")
        maybe_set_kwarg("preview_start")
        maybe_set_kwarg("preview_end")
        maybe_set_kwarg("genre")
        maybe_set_kwarg("media_type")
        maybe_set_kwarg("name")
        maybe_set_kwarg("artist")
        maybe_set_kwarg("charter")
        maybe_set_kwarg("album")
        maybe_set_kwarg("year")
        maybe_set_kwarg("music_stream")

        return cls(**kwargs)
