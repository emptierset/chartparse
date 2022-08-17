"""For functionality useful for all event objects.

.. _Google Python Style Guide:
    http://google.github.io/styleguide/pyguide.html

"""

from __future__ import annotations

import datetime
from typing import Final, Optional, Protocol, TypeVar

from chartparse.util import DictPropertiesEqMixin, DictReprMixin

EventT = TypeVar("EventT", bound="Event")


class TimestampGetterT(Protocol):
    def __call__(
        self, tick: int, resolution: int, start_bpm_event_index: int = ...
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

    _proximal_bpm_event_index: Optional[int]

    def __init__(
        self,
        tick: int,
        timestamp: datetime.timedelta,
        proximal_bpm_event_idx: Optional[int] = None,
    ) -> None:
        self.tick = tick
        self.timestamp = timestamp
        self._proximal_bpm_event_index = proximal_bpm_event_idx

    # TODO: Should this really be a staticmethod?
    @staticmethod
    def calculate_timestamp(
        tick: int,
        prev_event: Optional[EventT],
        timestamp_getter: TimestampGetterT,
        resolution: int,
    ) -> tuple[datetime.timedelta, int]:
        if prev_event is None:
            return datetime.timedelta(0), 0
        start_bpm_event_index = (
            prev_event._proximal_bpm_event_index
            if prev_event._proximal_bpm_event_index is not None
            else 0
        )
        return timestamp_getter(tick, resolution, start_bpm_event_index=start_bpm_event_index)

    # TODO: Figure out a way for the final closing parenthesis to wrap _around_ any additional info
    # added by subclass __str__ implementations.
    def __str__(self) -> str:  # pragma: no cover
        to_join = [f"{type(self).__name__}(t@{self.tick:07})"]
        as_str = (
            str(self.timestamp)
            if self.timestamp.total_seconds() > 0
            else f"{self.timestamp}.000000"
        )
        to_join.append(f": {as_str}")
        return "".join(to_join)
