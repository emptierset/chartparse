"""Functionality useful for all event track objects.

Most notably, :class:`~chartparse.instrument.InstrumentTrack`, :class:`~chartparse.sync.SyncTrack`,
and :class:`~chartparse.globalevents.GlobalEventsTrack` are considered to be event tracks.

.. _Google Python Style Guide:
    http://google.github.io/styleguide/pyguide.html

"""

from __future__ import annotations

import abc
import collections
import logging
import typing as typ
from collections.abc import Iterable, Sequence

import chartparse.globalevents
from chartparse.event import Event
from chartparse.exceptions import RegexNotMatchError, UnreachableError
from chartparse.instrument import StarPowerEvent, TrackEvent
from chartparse.sync import AnchorEvent, BPMEvent, BPMEvents, TimeSignatureEvent
from chartparse.tick import Ticks
from chartparse.util import DictPropertiesEqMixin, DictReprTruncatedSequencesMixin

logger = logging.getLogger(__name__)

_unparsable_line_msg_tmpl: typ.Final[str] = 'unparsable line: "{}" for types {}'


_ParsedDataT = typ.TypeVar("_ParsedDataT", bound=Event.ParsedData)


class ParsedDataMap(DictPropertiesEqMixin, DictReprTruncatedSequencesMixin):
    """A dict mapping ParsedData subtypes to lists of values of those types.

    TODO: Explain this in greater depth.
    """

    def __init__(self) -> None:
        self._dict: collections.defaultdict[typ.Any, typ.Any] = collections.defaultdict(list)

    def __getitem__(self, k: type[_ParsedDataT]) -> list[_ParsedDataT]:
        # Annotating _dict as [Any, Any] makes this a mandatory cast. I'm not aware of a better
        # annotation for _dict, as this entire class exists to circumvent the issue that I cannot
        # define a dict of type [type[T], list[T]] for any T. i.e. T is bound
        # https://github.com/python/typing/issues/548
        return typ.cast(list[_ParsedDataT], self._dict.__getitem__(k))


def parse_data_from_chart_lines(
    types: Sequence[type[_ParsedDataT]], lines: Iterable[str]
) -> ParsedDataMap:
    """Convert one or more chart lines into parsed data, and partition by type.

    Args:
        types: The types to which we should attempt to map each string in ``lines``. This function
            is more efficient if the types in `types` are ordered in descending frequency. That is,
            because it chooses the first type that matches, users should put the more common ones
            first.

        lines: An iterable of strings most likely from a Moonscraper ``.chart`` file.

    Returns:
        A dictionary mapping each type in ``types`` to a list of datas that were parsed into that
        type from lines in ``lines``.
    """
    m = ParsedDataMap()
    for line in lines:
        for t in types:
            try:
                data = t.from_chart_line(line)
            except RegexNotMatchError:
                continue
            m[t].append(data)
            break
        else:
            logger.warning(_unparsable_line_msg_tmpl.format(line, [t.__qualname__ for t in types]))
    return m


@typ.overload
def build_events_from_data(
    event_type: type[AnchorEvent],
    datas: Iterable[AnchorEvent.ParsedData],
    /,
) -> list[AnchorEvent]:
    ...  # pragma: no cover


@typ.overload
def build_events_from_data(
    event_type: type[BPMEvent],
    datas: Iterable[BPMEvent.ParsedData],
    resolution: Ticks,
    /,
) -> BPMEvents:
    ...  # pragma: no cover


@typ.overload
def build_events_from_data(
    event_type: type[TimeSignatureEvent],
    datas: Iterable[TimeSignatureEvent.ParsedData],
    bpm_events: BPMEvents,
    /,
) -> list[TimeSignatureEvent]:
    ...  # pragma: no cover


@typ.overload
def build_events_from_data(
    event_type: type[chartparse.globalevents.SectionEvent],
    datas: Iterable[chartparse.globalevents.SectionEvent.ParsedData],
    bpm_events: BPMEvents,
    /,
) -> list[chartparse.globalevents.SectionEvent]:
    ...  # pragma: no cover


@typ.overload
def build_events_from_data(
    event_type: type[chartparse.globalevents.LyricEvent],
    datas: Iterable[chartparse.globalevents.LyricEvent.ParsedData],
    bpm_events: BPMEvents,
    /,
) -> list[chartparse.globalevents.LyricEvent]:
    ...  # pragma: no cover


@typ.overload
def build_events_from_data(
    event_type: type[chartparse.globalevents.TextEvent],
    datas: Iterable[chartparse.globalevents.TextEvent.ParsedData],
    bpm_events: BPMEvents,
    /,
) -> list[chartparse.globalevents.TextEvent]:
    ...  # pragma: no cover


@typ.overload
def build_events_from_data(
    event_type: type[StarPowerEvent],
    datas: Iterable[StarPowerEvent.ParsedData],
    bpm_events: BPMEvents,
    /,
) -> list[StarPowerEvent]:
    ...  # pragma: no cover


@typ.overload
def build_events_from_data(
    event_type: type[TrackEvent],
    datas: Iterable[TrackEvent.ParsedData],
    bpm_events: BPMEvents,
    /,
) -> list[TrackEvent]:
    ...  # pragma: no cover


def build_events_from_data(
    event_type: type[BPMEvent]
    | type[TimeSignatureEvent]
    | type[AnchorEvent]
    | type[StarPowerEvent]
    | type[TrackEvent]
    | type[chartparse.globalevents.LyricEvent]
    | type[chartparse.globalevents.SectionEvent]
    | type[chartparse.globalevents.TextEvent],
    datas: Iterable[BPMEvent.ParsedData]
    | Iterable[TimeSignatureEvent.ParsedData]
    | Iterable[AnchorEvent.ParsedData]
    | Iterable[StarPowerEvent.ParsedData]
    | Iterable[TrackEvent.ParsedData]
    | Iterable[chartparse.globalevents.LyricEvent.ParsedData]
    | Iterable[chartparse.globalevents.SectionEvent.ParsedData]
    | Iterable[chartparse.globalevents.TextEvent.ParsedData],
    resolution_or_bpm_events_or_None: Ticks | BPMEvents | None = None,
    /,
) -> (
    BPMEvents
    | list[TimeSignatureEvent]
    | list[AnchorEvent]
    | list[StarPowerEvent]
    | list[TrackEvent]
    | list[chartparse.globalevents.LyricEvent]
    | list[chartparse.globalevents.SectionEvent]
    | list[chartparse.globalevents.TextEvent]
):
    def data_to_anchor_events(datas: Iterable[AnchorEvent.ParsedData]) -> list[AnchorEvent]:
        events: list[AnchorEvent] = []
        for data in datas:
            event = AnchorEvent.from_parsed_data(data)
            events.append(event)
        return events

    def data_to_bpm_events(datas: Iterable[BPMEvent.ParsedData], resolution: Ticks) -> BPMEvents:
        events: list[BPMEvent] = []
        for data in datas:
            prev_event = events[-1] if events else None
            events.append(BPMEvent.from_parsed_data(data, prev_event, resolution))
        return BPMEvents(events=events, resolution=resolution)

    # flake8 doesn't understand forward declaration of BPMNeedingEvent.
    BPMNeedingEventT = typ.TypeVar("BPMNeedingEventT", bound="BPMNeedingEvent")  # noqa: F821

    BPMNeedingParsedData = (
        TimeSignatureEvent.ParsedData
        | StarPowerEvent.ParsedData
        | TrackEvent.ParsedData
        # These are fully-qualified because there is otherwise a circular import.
        | chartparse.globalevents.LyricEvent.ParsedData
        | chartparse.globalevents.SectionEvent.ParsedData
        | chartparse.globalevents.TextEvent.ParsedData
    )

    BPMNeedingParsedDatas = (
        Iterable[TimeSignatureEvent.ParsedData]
        | Iterable[StarPowerEvent.ParsedData]
        | Iterable[TrackEvent.ParsedData]
        # These are fully-qualified because there is otherwise a circular import.
        | Iterable[chartparse.globalevents.LyricEvent.ParsedData]
        | Iterable[chartparse.globalevents.SectionEvent.ParsedData]
        | Iterable[chartparse.globalevents.TextEvent.ParsedData]
    )

    @typ.runtime_checkable
    class BPMNeedingEvent(typ.Protocol):
        @classmethod
        @abc.abstractmethod
        def from_parsed_data(
            cls: type[BPMNeedingEventT],
            data: BPMNeedingParsedData,
            prev_event: BPMNeedingEventT | None,
            bpm_events: BPMEvents,
        ) -> BPMNeedingEventT:
            ...  # pragma: no cover

    def data_to_events(
        event_type: type[BPMNeedingEventT],
        datas: BPMNeedingParsedDatas,
        bpm_events: BPMEvents,
    ) -> list[BPMNeedingEventT]:
        events: list[BPMNeedingEventT] = []
        for data in datas:
            prev_event = events[-1] if events else None
            events.append(event_type.from_parsed_data(data, prev_event, bpm_events))
        # TODO: Should we be able to validate a chart? This return value was previously sorted by
        # tick, but that's a non-method member and is therefore incompatible with runtime_checkable
        # protocols. Sorting here should be unnecessary because charts are probably fundamentally
        # broken if their events are not in tick order.
        return events

    if issubclass(event_type, AnchorEvent):
        datas = typ.cast(Iterable[AnchorEvent.ParsedData], datas)
        return data_to_anchor_events(datas)
    elif issubclass(event_type, BPMEvent):
        datas = typ.cast(Iterable[BPMEvent.ParsedData], datas)
        resolution = typ.cast(Ticks, resolution_or_bpm_events_or_None)
        return data_to_bpm_events(datas, resolution)
    elif issubclass(event_type, BPMNeedingEvent):
        datas = typ.cast(BPMNeedingParsedDatas, datas)
        bpm_events = typ.cast(BPMEvents, resolution_or_bpm_events_or_None)
        return data_to_events(event_type, datas, bpm_events)
    else:  # pragma: no cover
        raise UnreachableError("ifs are exhaustive")
