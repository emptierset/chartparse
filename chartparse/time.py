import typing as typ
from datetime import timedelta

from chartparse.exceptions import UnreachableError

Timestamp = typ.NewType("Timestamp", timedelta)
"""A specific time-moment in a chart.

Represented in terms of a positive ``datetime.timedelta`` relative to time zero.
"""


Seconds = typ.NewType("Seconds", float)
"""A duration represented by a floating point number of seconds."""


@typ.overload
def add(ts: Timestamp, other: Seconds) -> Timestamp:
    ...  # pragma: no cover


@typ.overload
def add(ts: Timestamp, other: timedelta) -> Timestamp:
    ...  # pragma: no cover


def add(ts: Timestamp, other: Seconds | timedelta) -> Timestamp:
    if isinstance(other, float):
        other_as_timedelta = timedelta(seconds=other)
        return Timestamp(ts + other_as_timedelta)
    elif isinstance(other, timedelta):
        return Timestamp(ts + other)
    else:  # pragma: no cover
        raise UnreachableError("other must be float or timedelta")
