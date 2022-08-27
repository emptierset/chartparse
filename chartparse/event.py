"""For functionality useful for all event objects.

.. _Google Python Style Guide:
    http://google.github.io/styleguide/pyguide.html

"""

from __future__ import annotations

import datetime
import typing
from typing import Final, Optional, Protocol, TypeVar

from chartparse.util import DictPropertiesEqMixin, DictReprMixin

EventT = TypeVar("EventT", bound="Event")


@typing.runtime_checkable
class TimestampAtTickSupporter(Protocol):
    resolution: int

    def timestamp_at_tick(
        self, tick: int, start_bpm_event_index: int = ...
    ) -> tuple[datetime.timedelta, int]:
        ...  # pragma: no cover


class Event(DictPropertiesEqMixin, DictReprMixin):
    """An event that occurs at a tick and timestamp in an :class:`~chartparse.track.EventTrack`.

    This is typically used only as a base class for more specialized subclasses. It implements an
    attractive ``__str__`` representation.
    """

    tick: Final[int]
    """The tick at which this event occurs."""

    timestamp: Final[datetime.timedelta]
    """The timestamp when this event occurs."""

    _proximal_bpm_event_index: Final[int]

    def __init__(
        self,
        tick: int,
        timestamp: datetime.timedelta,
        proximal_bpm_event_idx: int = 0,
    ) -> None:
        self.tick = tick
        self.timestamp = timestamp
        self._proximal_bpm_event_index = proximal_bpm_event_idx

    @staticmethod
    def calculate_timestamp(
        tick: int,
        prev_event: Optional[EventT],
        tatter: TimestampAtTickSupporter,
    ) -> tuple[datetime.timedelta, int]:
        return tatter.timestamp_at_tick(
            tick, start_bpm_event_index=prev_event._proximal_bpm_event_index if prev_event else 0
        )

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
