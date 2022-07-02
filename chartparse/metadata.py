from __future__ import annotations

import re
from collections.abc import Callable, Iterable
from typing import Any, ClassVar, Pattern, Type, TypeVar

import inflection

from chartparse.exceptions import RegexNotMatchError
from chartparse.track import HasSectionNameMixin
from chartparse.util import DictPropertiesEqMixin

MetadataT = TypeVar("MetadataT", bound="Metadata")


# TODO: Parse known attributes, rather than allow arbitrary injections.
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
class Metadata(HasSectionNameMixin, DictPropertiesEqMixin):
    """All of a :class:`~chartparse.chart.Chart` object's metadata.

    All attributes are set dynamically, but the following attributes are known and can be handled
    explicitly:
    ``Name``
    ``Artist``
    ``Charter``
    ``Album``
    ``Year``
    ``Offset``
    ``Resolution``
    ``Player2``
    ``Difficulty``
    ``PreviewStart``
    ``PreviewEnd``
    ``Genre``
    ``MediaType``
    ``MusicStream``.
    """

    section_name = "Song"

    resolution: int
    """The number of ticks for which a quarter note lasts."""

    # Known fields in the [Song] section and the functions that should be used
    # to process them.
    _field_transformers: ClassVar[dict[str, Callable[[Any], Any]]] = {
        "Name": str,
        "Artist": str,
        "Charter": str,
        "Album": str,
        "Year": str,
        "Offset": int,
        "Resolution": int,
        "Player2": str,
        "Difficulty": int,
        "PreviewStart": int,
        "PreviewEnd": int,
        "Genre": str,
        "MediaType": str,
        "MusicStream": str,
    }

    _regex: ClassVar[str] = r"^\s*?([A-Za-z0-9]+?)\s=\s\"?(.*?)\"?\s*?$"
    _regex_prog: ClassVar[Pattern[str]] = re.compile(_regex)

    def __init__(self, injections: dict[str, Any]) -> None:
        """Initializes instance attributes from a dictionary.

        Args:
            injections: A dictionary mapping instance attribute names to their values.
        """
        for field_name, value in injections.items():
            setattr(self, field_name, value)

    @classmethod
    def from_chart_lines(cls: Type[MetadataT], lines: Iterable[str]) -> MetadataT:
        """Initializes instance attributes by parsing an iterable of strings.

        Args:
            lines: Most likely from a Moonscraper ``.chart``.
        """
        injections = dict()
        for line in lines:
            m = cls._regex_prog.match(line)
            if not m:
                raise RegexNotMatchError(cls._regex, line)
            field_name, raw_value = m.group(1), m.group(2)
            if field_name in cls._field_transformers:
                transformed_value = cls._field_transformers[field_name](raw_value)
                value_to_set = transformed_value
            else:
                # TODO: Log that transformer couldn't be found.
                value_to_set = raw_value
            pythonic_field_name = inflection.underscore(field_name)
            injections[pythonic_field_name] = value_to_set
        return cls(injections)

    def __repr__(self) -> str:  # pragma: no cover
        return str(self.__dict__)
