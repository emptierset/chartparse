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
from collections.abc import Iterable, Sequence

from chartparse.event import Event
from chartparse.exceptions import RegexNotMatchError, UnreachableError
from chartparse.sync import AnchorEvent, BPMEvents
from chartparse.tick import Ticks

if typ.TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Callable

    from chartparse.globalevents import LyricEvent, SectionEvent, TextEvent
    from chartparse.instrument import StarPowerEvent, TrackEvent
    from chartparse.sync import BPMEvent, TimeSignatureEvent

logger = logging.getLogger(__name__)

_unparsable_line_msg_tmpl: typ.Final[str] = 'unparsable line: "{}" for types {}'


class ParsedDataDict(collections.defaultdict):
    def __init__(self):
        super().__init__(list)

    def __getitem__(self, k: type[Event.ParsedData._Self]) -> list[Event.ParsedData._Self]:
        return super().__getitem__(k)

    def __setitem__(
        self, k: type[Event.ParsedData._Self], v: list[Event.ParsedData._Self]
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
    datas: Iterable[AnchorEvent.ParsedData],
    from_data_fn: Callable[[AnchorEvent.ParsedData], AnchorEvent],
    /,
) -> list[AnchorEvent]:
    ...  # pragma: no cover


@typ.overload
def build_events_from_data(
    datas: Iterable[BPMEvent.ParsedData],
    from_data_fn: Callable[
        [
            BPMEvent.ParsedData,
            BPMEvent | None,
            Ticks,
        ],
        BPMEvent,
    ],
    resolution: Ticks,
    /,
) -> BPMEvents:
    ...  # pragma: no cover


@typ.overload
def build_events_from_data(
    datas: Iterable[TimeSignatureEvent.ParsedData],
    from_data_fn: Callable[
        [
            TimeSignatureEvent.ParsedData,
            TimeSignatureEvent | None,
            BPMEvents,
        ],
        TimeSignatureEvent,
    ],
    bpm_events: BPMEvents,
    /,
) -> list[TimeSignatureEvent]:
    ...  # pragma: no cover


@typ.overload
def build_events_from_data(
    datas: Iterable[SectionEvent.ParsedData],
    from_data_fn: Callable[
        [
            SectionEvent.ParsedData,
            SectionEvent | None,
            BPMEvents,
        ],
        SectionEvent,
    ],
    bpm_events: BPMEvents,
    /,
) -> list[SectionEvent]:
    ...  # pragma: no cover


@typ.overload
def build_events_from_data(
    datas: Iterable[LyricEvent.ParsedData],
    from_data_fn: Callable[
        [
            LyricEvent.ParsedData,
            LyricEvent | None,
            BPMEvents,
        ],
        LyricEvent,
    ],
    bpm_events: BPMEvents,
    /,
) -> list[LyricEvent]:
    ...  # pragma: no cover


@typ.overload
def build_events_from_data(
    datas: Iterable[TextEvent.ParsedData],
    from_data_fn: Callable[
        [
            TextEvent.ParsedData,
            TextEvent | None,
            BPMEvents,
        ],
        TextEvent,
    ],
    bpm_events: BPMEvents,
    /,
) -> list[TextEvent]:
    ...  # pragma: no cover


@typ.overload
def build_events_from_data(
    datas: Iterable[StarPowerEvent.ParsedData],
    from_data_fn: Callable[
        [
            StarPowerEvent.ParsedData,
            StarPowerEvent | None,
            BPMEvents,
        ],
        StarPowerEvent,
    ],
    bpm_events: BPMEvents,
    /,
) -> list[StarPowerEvent]:
    ...  # pragma: no cover


@typ.overload
def build_events_from_data(
    datas: Iterable[TrackEvent.ParsedData],
    from_data_fn: Callable[
        [
            TrackEvent.ParsedData,
            TrackEvent | None,
            BPMEvents,
        ],
        TrackEvent,
    ],
    bpm_events: BPMEvents,
    /,
) -> list[TrackEvent]:
    ...  # pragma: no cover


def build_events_from_data(datas, from_data_fn, resolution_or_bpm_events_or_None=None, /):
    events = []
    for data in datas:
        if isinstance(data, AnchorEvent.ParsedData):
            event = from_data_fn(data)
            events.append(event)
        else:
            prev_event = events[-1] if events else None
            event = from_data_fn(data, prev_event, resolution_or_bpm_events_or_None)
            events.append(event)
    if isinstance(resolution_or_bpm_events_or_None, int):
        # Using BPMEvent.ParsedData.
        # In this case, BPMEvents must already be in increasing tick order, by definition.
        return BPMEvents(events=events, resolution=resolution_or_bpm_events_or_None)
    elif resolution_or_bpm_events_or_None is None:
        # Using AnchorEvent.ParsedData.
        # In this case, AnchorEvents must already be in increasing tick order, by definition.
        return events
    elif isinstance(resolution_or_bpm_events_or_None, BPMEvents):
        # TODO: Should we instead optionally validate a chart, which allows us to assume everything
        # is sorted? etc.
        return sorted(events, key=lambda e: e.tick)
    else:  # pragma: no cover
        raise UnreachableError("resolution_or_bpm_events_or_None must be one of the named types")
