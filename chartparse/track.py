"""For functionality useful for all event track objects.

Most notably, :class:`~chartparse.instrument.InstrumentTrack`, :class:`~chartparse.sync.SyncTrack`,
and :class:`~chartparse.globalevents.GlobalEventsTrack` are considered to be event tracks.

.. _Google Python Style Guide:
    http://google.github.io/styleguide/pyguide.html

"""

from __future__ import annotations

import collections
import logging
import typing as typ
from collections.abc import Callable, Iterable, Sequence

import chartparse.globalevents
import chartparse.instrument
import chartparse.sync
from chartparse.event import Event, TimestampAtTickSupporter
from chartparse.exceptions import ProgrammerError, RegexNotMatchError

logger = logging.getLogger(__name__)
_unparsable_line_msg_tmpl: typ.Final[str] = 'unparsable line: "{}" for types {}'


class ParsedDataDict(collections.defaultdict):
    def __init__(self):
        super().__init__(list)

    def __getitem__(self, k: type[Event.ParsedData._SelfT]) -> list[Event.ParsedData._SelfT]:
        return super().__getitem__(k)

    def __setitem__(
        self, k: type[Event.ParsedData._SelfT], v: list[Event.ParsedData._SelfT]
    ) -> None:
        return super().__setitem__(k, v)


def parse_data_from_chart_lines(
    types: Sequence[type[Event.ParsedData]], lines: Iterable[str]
) -> ParsedDataDict:
    """Convert one or more chart lines into parsed data, and partition by type.

    Args:
        types: The types to which we should attempt to map each string in ``lines``. This function
            is more efficient if the types in `types` are ordered in descending frequency. That is,
            because it chooses the first type that matches, users should put the more common ones
            first.
        lines: An iterable of strings most likely from a Moonscraper ``.chart``.

    Returns:
        A dictionary mapping each type in ``types`` to a list of datas that were parsed into that
        type from lines in ``lines``.
    """
    d = ParsedDataDict()
    for line in lines:
        for t in types:
            try:
                data = t.from_chart_line(line)
            except RegexNotMatchError:
                continue
            d[t].append(data)
            break
        else:
            logger.warning(_unparsable_line_msg_tmpl.format(line, [t.__qualname__ for t in types]))
    return d


@typ.overload
def build_events_from_data(
    datas: Iterable[chartparse.sync.BPMEvent.ParsedData],
    from_data_fn: Callable[
        [
            chartparse.sync.BPMEvent.ParsedData,
            chartparse.sync.BPMEvent | None,
            int,
        ],
        chartparse.sync.BPMEvent,
    ],
    resolution: int,
    /,
) -> list[chartparse.sync.BPMEvent]:
    ...  # pragma: no cover


@typ.overload
def build_events_from_data(
    datas: Iterable[chartparse.sync.TimeSignatureEvent.ParsedData],
    from_data_fn: Callable[
        [
            chartparse.sync.TimeSignatureEvent.ParsedData,
            chartparse.sync.TimeSignatureEvent | None,
            TimestampAtTickSupporter,
        ],
        chartparse.sync.TimeSignatureEvent,
    ],
    tatter: TimestampAtTickSupporter,
    /,
) -> list[chartparse.sync.TimeSignatureEvent]:
    ...  # pragma: no cover


@typ.overload
def build_events_from_data(
    datas: Iterable[chartparse.globalevents.SectionEvent.ParsedData],
    from_data_fn: Callable[
        [
            chartparse.globalevents.SectionEvent.ParsedData,
            chartparse.globalevents.SectionEvent | None,
            TimestampAtTickSupporter,
        ],
        chartparse.globalevents.SectionEvent,
    ],
    tatter: TimestampAtTickSupporter,
    /,
) -> list[chartparse.globalevents.SectionEvent]:
    ...  # pragma: no cover


@typ.overload
def build_events_from_data(
    datas: Iterable[chartparse.globalevents.LyricEvent.ParsedData],
    from_data_fn: Callable[
        [
            chartparse.globalevents.LyricEvent.ParsedData,
            chartparse.globalevents.LyricEvent | None,
            TimestampAtTickSupporter,
        ],
        chartparse.globalevents.LyricEvent,
    ],
    tatter: TimestampAtTickSupporter,
    /,
) -> list[chartparse.globalevents.LyricEvent]:
    ...  # pragma: no cover


@typ.overload
def build_events_from_data(
    datas: Iterable[chartparse.globalevents.TextEvent.ParsedData],
    from_data_fn: Callable[
        [
            chartparse.globalevents.TextEvent.ParsedData,
            chartparse.globalevents.TextEvent | None,
            TimestampAtTickSupporter,
        ],
        chartparse.globalevents.TextEvent,
    ],
    tatter: TimestampAtTickSupporter,
    /,
) -> list[chartparse.globalevents.TextEvent]:
    ...  # pragma: no cover


@typ.overload
def build_events_from_data(
    datas: Iterable[chartparse.instrument.StarPowerEvent.ParsedData],
    from_data_fn: Callable[
        [
            chartparse.instrument.StarPowerEvent.ParsedData,
            chartparse.instrument.StarPowerEvent | None,
            TimestampAtTickSupporter,
        ],
        chartparse.instrument.StarPowerEvent,
    ],
    tatter: TimestampAtTickSupporter,
    /,
) -> list[chartparse.instrument.StarPowerEvent]:
    ...  # pragma: no cover


def build_events_from_data(datas, from_data_fn, resolution_or_tatter, /):
    events = []
    for data in datas:
        prev_event = events[-1] if events else None
        event = from_data_fn(data, prev_event, resolution_or_tatter)
        events.append(event)
    if isinstance(resolution_or_tatter, int):  # using BPMEvent.ParsedData
        # In this case, BPMEvents must already be in increasing tick order, by definition.
        return events
    elif isinstance(resolution_or_tatter, TimestampAtTickSupporter):
        return sorted(events, key=lambda e: e.tick)
    else:
        raise ProgrammerError  # pragma: no cover
