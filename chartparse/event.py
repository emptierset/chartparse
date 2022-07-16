"""For functionality useful for all event objects.

.. _Google Python Style Guide:
    http://google.github.io/styleguide/pyguide.html

"""

from __future__ import annotations

import datetime
from typing import Optional, TypeVar

from chartparse.util import DictPropertiesEqMixin, DictReprMixin

EventT = TypeVar("EventT", bound="Event")


class Event(DictPropertiesEqMixin, DictReprMixin):
    """An event that occurs at a specific tick in an :class:`~chartparse.track.EventTrack`.

    This is typically used only as a base class for more specialized subclasses. It implements an
    attractive ``__str__`` representation.
    """

    tick: int
    """The tick at which this event occurs."""

    # TODO: Figure out how to accurately represent it in the type system that this is set later.
    # Might involve wrapping ``Event`` in a subclass that has ``timestamp``.
    timestamp: datetime.timedelta
    """The timestamp when this event occurs.

    This is not set in ``__init__``; it must be set manually, most likely via
    :meth:`~chartparse.chart._populate_event_timestamps` or
    :meth:`~chartparse.chart._populate_bpm_event_timestamps`.
    """

    def __init__(self, tick: int, timestamp: Optional[datetime.timedelta] = None) -> None:
        self.tick = tick
        if timestamp is not None:
            self.timestamp = timestamp

    # TODO: Figure out a way for the final closing parenthesis to wrap _around_ any additional info
    # added by subclass __str__ implementations.
    def __str__(self) -> str:  # pragma: no cover
        to_join = [f"{type(self).__name__}(t@{self.tick:07}"]
        if hasattr(self, "timestamp"):
            as_str = (
                str(self.timestamp)
                if self.timestamp.total_seconds() > 0
                else f"{self.timestamp}.000000"
            )
            to_join.append(f" {as_str}")
        to_join.append(")")
        return "".join(to_join)
