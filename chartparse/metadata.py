"""For representing a chart's metadata, such as musical artist.

You should not need to create any of this module's objects manually; please instead create a
:class:`~chartparse.chart.Chart` and inspect its attributes via that object.

.. _Google Python Style Guide:
    http://google.github.io/styleguide/pyguide.html

"""

from __future__ import annotations

import dataclasses
import enum
import re
import typing as typ
from collections.abc import Callable

from chartparse.exceptions import MissingRequiredField, RegexNotMatchError, raise_
from chartparse.util import DictPropertiesEqMixin, DictReprMixin

if typ.TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Iterable

SnakeCaseFieldName = typ.Literal[
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
    "guitar_stream",
    "rhythm_stream",
    "bass_stream",
    "drum_stream",
    "drum2_stream",
    "drum3_stream",
    "drum4_stream",
    "vocal_stream",
    "keys_stream",
    "crowd_stream",
]

PascalCaseFieldName = typ.Literal[
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
    "GuitarStream",
    "RhythmStream",
    "BassStream",
    "DrumStream",
    "Drum2Stream",
    "Drum3Stream",
    "Drum4Stream",
    "VocalStream",
    "KeysStream",
    "CrowdStream",
]


@enum.unique
class Player2Instrument(enum.Enum):
    """The instrument type of the co-op guitar chart in Guitar Hero 3."""

    BASS = "bass"
    RHYTHM = "rhythm"


FieldValue = int | str | Player2Instrument

FieldValueParser = Callable[[str], FieldValue]


class _FieldValuesDict(typ.TypedDict, total=False):
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
    guitar_stream: str
    rhythm_stream: str
    bass_stream: str
    drum_stream: str
    drum2_stream: str
    drum3_stream: str
    drum4_stream: str
    vocal_stream: str
    keys_stream: str
    crowd_stream: str


class _FieldParsingSpec(object):
    """A bundle of data necessary to parse a field from a ``.chart`` file."""

    regex: str
    regex_prog: typ.Pattern[str]

    processing_fn: FieldValueParser

    def __init__(self, regex: str, processing_fn: FieldValueParser) -> None:
        self.regex = regex
        self.regex_prog = re.compile(self.regex)
        self.processing_fn = processing_fn

    @staticmethod
    def make_field_regex(
        field_name: PascalCaseFieldName, value_regex: str, is_value_quoted: bool
    ) -> str:
        to_join = [rf"^\s*?{field_name} = "]
        if is_value_quoted:
            to_join.append(r'"')
        to_join.append(rf"({value_regex})")
        if is_value_quoted:
            to_join.append(r'"')
        to_join.append(r"\s*?$")
        return "".join(to_join)


@typ.final
class _IntFieldSpec(_FieldParsingSpec):
    def __init__(self, field_name: PascalCaseFieldName) -> None:
        super().__init__(self.make_int_field_regex(field_name), int)

    @staticmethod
    def make_int_field_regex(field_name: PascalCaseFieldName) -> str:
        return _FieldParsingSpec.make_field_regex(field_name, r"\d+?", False)


@typ.final
class _MultiwordStrFieldSpec(_FieldParsingSpec):
    def __init__(self, field_name: PascalCaseFieldName) -> None:
        super().__init__(self.make_multiword_str_field_regex(field_name), str)

    @staticmethod
    def make_multiword_str_field_regex(field_name: PascalCaseFieldName) -> str:
        return _FieldParsingSpec.make_field_regex(field_name, r".+?", True)


@typ.final
class _QuotelessStrFieldSpec(_FieldParsingSpec):
    def __init__(
        self,
        field_name: PascalCaseFieldName,
        processing_fn: FieldValueParser,
    ) -> None:
        super().__init__(self.make_quoteless_str_field_regex(field_name), processing_fn)

    @staticmethod
    def make_quoteless_str_field_regex(field_name: PascalCaseFieldName) -> str:
        return _FieldParsingSpec.make_field_regex(field_name, r'[^"]+?', False)


class _FieldParsingSpecDict(typ.TypedDict):
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
    guitar_stream: _FieldParsingSpec
    rhythm_stream: _FieldParsingSpec
    bass_stream: _FieldParsingSpec
    drum_stream: _FieldParsingSpec
    drum2_stream: _FieldParsingSpec
    drum3_stream: _FieldParsingSpec
    drum4_stream: _FieldParsingSpec
    vocal_stream: _FieldParsingSpec
    keys_stream: _FieldParsingSpec
    crowd_stream: _FieldParsingSpec


_field_parsing_specs: _FieldParsingSpecDict = {
    "resolution": _IntFieldSpec("Resolution"),
    "offset": _IntFieldSpec("Offset"),
    "player2": _QuotelessStrFieldSpec("Player2", processing_fn=lambda s: Player2Instrument(s)),
    "difficulty": _IntFieldSpec("Difficulty"),
    "preview_start": _IntFieldSpec("PreviewStart"),
    "preview_end": _IntFieldSpec("PreviewEnd"),
    "genre": _MultiwordStrFieldSpec("Genre"),
    "media_type": _MultiwordStrFieldSpec("MediaType"),
    "name": _MultiwordStrFieldSpec("Name"),
    "artist": _MultiwordStrFieldSpec("Artist"),
    "charter": _MultiwordStrFieldSpec("Charter"),
    "album": _MultiwordStrFieldSpec("Album"),
    "year": _MultiwordStrFieldSpec("Year"),
    "music_stream": _MultiwordStrFieldSpec("MusicStream"),
    "guitar_stream": _MultiwordStrFieldSpec("GuitarStream"),
    "rhythm_stream": _MultiwordStrFieldSpec("RhythmStream"),
    "bass_stream": _MultiwordStrFieldSpec("BassStream"),
    "drum_stream": _MultiwordStrFieldSpec("DrumStream"),
    "drum2_stream": _MultiwordStrFieldSpec("Drum2Stream"),
    "drum3_stream": _MultiwordStrFieldSpec("Drum3Stream"),
    "drum4_stream": _MultiwordStrFieldSpec("Drum4Stream"),
    "vocal_stream": _MultiwordStrFieldSpec("VocalStream"),
    "keys_stream": _MultiwordStrFieldSpec("KeysStream"),
    "crowd_stream": _MultiwordStrFieldSpec("CrowdStream"),
}


@typ.final
@dataclasses.dataclass(frozen=True, kw_only=True)
class Metadata(DictPropertiesEqMixin, DictReprMixin):
    """All of a :class:`~chartparse.chart.Chart` object's metadata.

    This is a ``frozen``, ``kw_only`` dataclass.
    """

    _Self = typ.TypeVar("_Self", bound="Metadata")

    section_name: typ.ClassVar[str] = "Song"
    """The name of this track's section in a ``.chart`` file."""

    resolution: int
    """The number of ticks for which a quarter note lasts."""

    offset: int = 0
    """The number of seconds in time before tick 0 is reached.

    This is a legacy field and should most likely be ignored.
    """

    player2: Player2Instrument = Player2Instrument.BASS
    """The instrument type of the co-op guitar chart in Guitar Hero 3."""

    difficulty: int = 0
    """The perceived difficulty to play the chart.

    This is often referred to as "intensity".
    """

    preview_start: int = 0
    """The number of seconds into the song at which the song preview should start.

    Might not actually be seconds. Typically, ``preview_start_time`` in ``song.ini`` is respected
    for Clone Hero instead.
    """

    preview_end: int = 0
    """The number of seconds into the song at which the song preview should end.

    Might not actually be seconds. Clone Hero just plays a preview of a particular length starting
    at ``preview_start_time`` in ``song.ini``, so this is unlikely to ever do anything in modern
    Guitar Hero.
    """

    genre: str = "rock"
    """The genre of the chart's song."""

    media_type: str = "cd"
    """The type of media from which the chart's song originates."""

    name: str | None = None
    """The name of the chart's song."""

    artist: str | None = None
    """The name of the chart's song's artist."""

    charter: str | None = None
    """The user who made this chart."""

    album: str | None = None
    """The name of the chart's song's album."""

    year: str | None = None
    """The year the chart's song came out.

    This is formatted as, e.g. ", 2018" because it saved time when importing into GHTCP (Guitar
    Hero Three Control Panel).
    """

    music_stream: str | None = None
    """The filename of the main music audio file."""

    guitar_stream: str | None = None
    """The filename of the guitar audio file."""

    rhythm_stream: str | None = None
    """The filename of the rhythm audio file."""

    bass_stream: str | None = None
    """The filename of the bass audio file."""

    drum_stream: str | None = None
    """The filename of the drum audio file."""

    drum2_stream: str | None = None
    """The filename of the drum2 audio file."""

    drum3_stream: str | None = None
    """The filename of the drum3 audio file."""

    drum4_stream: str | None = None
    """The filename of the drum4 audio file."""

    vocal_stream: str | None = None
    """The filename of the vocal audio file."""

    keys_stream: str | None = None
    """The filename of the keys audio file."""

    crowd_stream: str | None = None
    """The filename of the crowd audio file."""

    @classmethod
    def from_chart_lines(cls: type[_Self], lines_iter: Iterable[str]) -> _Self:
        """Initializes instance attributes by parsing an iterable of strings.

        Args:
            lines: An iterable of strings most likely from a Moonscraper ``.chart``.
        """
        kwargs: _FieldValuesDict = dict()

        lines = list(lines_iter)

        def set_kwarg(
            field_name: SnakeCaseFieldName,
            regex_not_match_callback: Callable[[], None] | None = None,
        ) -> None:
            maybe_set_kwarg(
                field_name,
                regex_not_match_callback=lambda: raise_(MissingRequiredField(field_name)),
            )

        def maybe_set_kwarg(
            field_name: SnakeCaseFieldName,
            regex_not_match_callback: Callable[[], None] | None = None,
        ) -> None:
            try:
                kwargs[field_name] = parse_all_lines_for_field(field_name)
            except RegexNotMatchError:
                if regex_not_match_callback is not None:
                    regex_not_match_callback()

        def parse_all_lines_for_field(field_name: SnakeCaseFieldName) -> FieldValue:
            regex_prog = _field_parsing_specs[field_name].regex_prog
            for line in lines:
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
        maybe_set_kwarg("guitar_stream")
        maybe_set_kwarg("rhythm_stream")
        maybe_set_kwarg("bass_stream")
        maybe_set_kwarg("drum_stream")
        maybe_set_kwarg("drum2_stream")
        maybe_set_kwarg("drum3_stream")
        maybe_set_kwarg("drum4_stream")
        maybe_set_kwarg("vocal_stream")
        maybe_set_kwarg("keys_stream")
        maybe_set_kwarg("crowd_stream")

        return cls(**kwargs)
