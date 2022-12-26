"""For functionality useful for all event objects.

.. _Google Python Style Guide:
    http://google.github.io/styleguide/pyguide.html

"""

from __future__ import annotations

import abc
import dataclasses
import datetime
import typing as typ

from chartparse.util import DictPropertiesEqMixin, DictReprMixin


@typ.runtime_checkable
class TimestampAtTickSupporter(typ.Protocol):
    @property
    def resolution(self) -> int:
        ...  # pragma: no cover

    def timestamp_at_tick(
        self, tick: int, proximal_bpm_event_index: int = ...
    ) -> tuple[datetime.timedelta, int]:
        ...  # pragma: no cover


class Event(DictPropertiesEqMixin, DictReprMixin):
    """An event that occurs at a tick and timestamp in an :class:`~chartparse.track.EventTrack`.

    This is typically used only as a base class for more specialized subclasses. It implements an
    attractive ``__str__`` representation.
    """

    tick: typ.Final[int]
    """The tick at which this event occurs."""

    timestamp: typ.Final[datetime.timedelta]
    """The timestamp when this event occurs."""

    _proximal_bpm_event_index: typ.Final[int]

    def __init__(
        self,
        tick: int,
        timestamp: datetime.timedelta,
        proximal_bpm_event_index: int = 0,
    ) -> None:
        self.tick = tick
        self.timestamp = timestamp
        self._proximal_bpm_event_index = proximal_bpm_event_index

    # TODO: Figure out a way for the final closing parenthesis to wrap _around_ any additional info
    # added by subclass __str__ implementations.
    def __str__(self) -> str:  # pragma: no cover
        to_join = [f"{type(self).__name__}(t@{self.tick:07})"]
        as_str = (
            str(self.timestamp)
            if not self.timestamp.total_seconds().is_integer()
            else f"{self.timestamp}.000000"
        )
        to_join.append(f": {as_str}")
        return "".join(to_join)

    # NOTE: ignored mypy here per https://stackoverflow.com/a/70999704/6041556.
    @dataclasses.dataclass(kw_only=True, frozen=True)  # type: ignore[misc]
    class ParsedData(abc.ABC):
        tick: int
        """The tick at which the event represented by this data occurs."""

        _SelfT = typ.TypeVar("_SelfT", bound="Event.ParsedData")

        @classmethod
        @abc.abstractmethod
        def from_chart_line(cls: type[_SelfT], line: str) -> _SelfT:
            ...  # pragma: no cover
