"""For functionality useful for all event track objects.

Most notably, :class:`~chartparse.instrument.InstrumentTrack`, :class:`~chartparse.sync.SyncTrack`,
and :class:`~chartparse.globalevents.GlobalEventsTrack` are considered to be event tracks.

.. _Google Python Style Guide:
    http://google.github.io/styleguide/pyguide.html

"""

from __future__ import annotations

import collections
import logging
import typing
from collections.abc import Callable, Iterable, Sequence
from typing import Final, Optional, Type

import chartparse.globalevents
import chartparse.instrument
import chartparse.sync
from chartparse.datastructures import ImmutableSortedList
from chartparse.event import Event, TimestampAtTickSupporter
from chartparse.exceptions import ProgrammerError, RegexNotMatchError

logger = logging.getLogger(__name__)
_unparsable_line_msg_tmpl: Final[str] = 'unparsable line: "{}" for types {}'


def parse_data_from_chart_lines(
    types: Sequence[Type[Event.ParsedData]],
    lines: Iterable[str],
) -> dict[Type[Event.ParsedData], list[Event.ParsedData]]:
    """Convert one or more chart lines into parsed data, and partition by type.

    Args:
        types: The types to which we should attempt to map each string in ``lines``. This function
            is more efficient if the types in `types` are ordered in descending frequency. That is,
            because it chooses the first type that matches, users should put the more common ones
            first.
        lines: An iterable of strings most likely from a Moonscraper ``.chart``.

    Returns:
        A dictionary mapping each type in ``types`` to a list of datas that were parsed into that
        type from lines in ``lines``. In reality, this maps ``Type[t]`` to ``list[t]`` for each
        ``t`` in ``types``, but this cannot be represented in mypy. Callers of this function will
        need to manually narrow types of the the dictionary entries they care about, most likely
        using ``typing.cast``.

    Raises:
        ValueError: If two parsed datas occur at the same tick and are not typed of the same
            subclass of :class:`~chartparse.event.Event.CoalescableParsedData`.
    """
    d: collections.defaultdict[
        Type[Event.ParsedData], list[Event.ParsedData]
    ] = collections.defaultdict(list)
    for line in lines:
        for t in types:
            try:
                data = t.from_chart_line(line)
            except RegexNotMatchError:
                continue
            prev_data = d[t][-1] if d[t] else None
            if prev_data is None or prev_data.tick != data.tick:
                d[t].append(data)
            elif isinstance(prev_data, Event.CoalescableParsedData):
                # TODO: Optimize this to precompute which types are coalescable.
                # This cast is safe because each element of d[t] is the same type.
                prev_data.coalesce_from_other(typing.cast(Event.CoalescableParsedData, data))
            else:
                raise ValueError(
                    f"cannot handle additional parsed data of type {t} at tick {data.tick}"
                )
            break
        else:
            logger.warning(_unparsable_line_msg_tmpl.format(line, [t.__qualname__ for t in types]))

    return d


@typing.overload
def build_events_from_data(
    datas: Iterable[chartparse.sync.BPMEvent.ParsedData],
    from_data_fn: Callable[
        [
            chartparse.sync.BPMEvent.ParsedData,
            Optional[chartparse.sync.BPMEvent],
            int,
        ],
        chartparse.sync.BPMEvent,
    ],
    resolution: int,
    /,
) -> ImmutableSortedList[chartparse.sync.BPMEvent]:
    ...  # pragma: no cover


@typing.overload
def build_events_from_data(
    datas: Iterable[chartparse.sync.TimeSignatureEvent.ParsedData],
    from_data_fn: Callable[
        [
            chartparse.sync.TimeSignatureEvent.ParsedData,
            Optional[chartparse.sync.TimeSignatureEvent],
            TimestampAtTickSupporter,
        ],
        chartparse.sync.TimeSignatureEvent,
    ],
    tatter: TimestampAtTickSupporter,
    /,
) -> ImmutableSortedList[chartparse.sync.TimeSignatureEvent]:
    ...  # pragma: no cover


@typing.overload
def build_events_from_data(
    datas: Iterable[chartparse.globalevents.SectionEvent.ParsedData],
    from_data_fn: Callable[
        [
            chartparse.globalevents.SectionEvent.ParsedData,
            Optional[chartparse.globalevents.SectionEvent],
            TimestampAtTickSupporter,
        ],
        chartparse.globalevents.SectionEvent,
    ],
    tatter: TimestampAtTickSupporter,
    /,
) -> ImmutableSortedList[chartparse.globalevents.SectionEvent]:
    ...  # pragma: no cover


@typing.overload
def build_events_from_data(
    datas: Iterable[chartparse.globalevents.LyricEvent.ParsedData],
    from_data_fn: Callable[
        [
            chartparse.globalevents.LyricEvent.ParsedData,
            Optional[chartparse.globalevents.LyricEvent],
            TimestampAtTickSupporter,
        ],
        chartparse.globalevents.LyricEvent,
    ],
    tatter: TimestampAtTickSupporter,
    /,
) -> ImmutableSortedList[chartparse.globalevents.LyricEvent]:
    ...  # pragma: no cover


@typing.overload
def build_events_from_data(
    datas: Iterable[chartparse.globalevents.TextEvent.ParsedData],
    from_data_fn: Callable[
        [
            chartparse.globalevents.TextEvent.ParsedData,
            Optional[chartparse.globalevents.TextEvent],
            TimestampAtTickSupporter,
        ],
        chartparse.globalevents.TextEvent,
    ],
    tatter: TimestampAtTickSupporter,
    /,
) -> ImmutableSortedList[chartparse.globalevents.TextEvent]:
    ...  # pragma: no cover


@typing.overload
def build_events_from_data(
    datas: Iterable[chartparse.instrument.StarPowerEvent.ParsedData],
    from_data_fn: Callable[
        [
            chartparse.instrument.StarPowerEvent.ParsedData,
            Optional[chartparse.instrument.StarPowerEvent],
            TimestampAtTickSupporter,
        ],
        chartparse.instrument.StarPowerEvent,
    ],
    tatter: TimestampAtTickSupporter,
    /,
) -> ImmutableSortedList[chartparse.instrument.StarPowerEvent]:
    ...  # pragma: no cover


def build_events_from_data(datas, from_data_fn, resolution_or_tatter, /):
    events = []
    for data in datas:
        prev_event = events[-1] if events else None
        event = from_data_fn(data, prev_event, resolution_or_tatter)
        events.append(event)
    if isinstance(resolution_or_tatter, int):  # using BPMEvent.ParsedData
        # In this case, BPMEvents must already be in increasing tick order, by definition.
        return ImmutableSortedList(events, already_sorted=True)
    elif isinstance(resolution_or_tatter, TimestampAtTickSupporter):
        return ImmutableSortedList(events, key=lambda e: e.tick)
    else:
        raise ProgrammerError  # pragma: no cover
