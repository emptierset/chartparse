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
from chartparse.util import DictPropertiesEqMixin, DictReprTruncatedSequencesMixin

if typ.TYPE_CHECKING:  # pragma: no cover
    from chartparse.globalevents import LyricEvent, SectionEvent, TextEvent
    from chartparse.instrument import StarPowerEvent, TrackEvent
    from chartparse.sync import BPMEvent, TimeSignatureEvent

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

        lines: An iterable of strings most likely from a Moonscraper ``.chart``.

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
    event_type: type[SectionEvent],
    datas: Iterable[SectionEvent.ParsedData],
    bpm_events: BPMEvents,
    /,
) -> list[SectionEvent]:
    ...  # pragma: no cover


@typ.overload
def build_events_from_data(
    event_type: type[LyricEvent],
    datas: Iterable[LyricEvent.ParsedData],
    bpm_events: BPMEvents,
    /,
) -> list[LyricEvent]:
    ...  # pragma: no cover


@typ.overload
def build_events_from_data(
    event_type: type[TextEvent],
    datas: Iterable[TextEvent.ParsedData],
    bpm_events: BPMEvents,
    /,
) -> list[TextEvent]:
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


# TODO: Figure out htf to annotate this.
def build_events_from_data(event_type, datas, resolution_or_bpm_events_or_None=None, /):  # type: ignore  # noqa
    events = []
    for data in datas:
        if isinstance(data, AnchorEvent.ParsedData):
            event = event_type.from_parsed_data(data)
            events.append(event)
        else:
            prev_event = events[-1] if events else None
            event = event_type.from_parsed_data(data, prev_event, resolution_or_bpm_events_or_None)
            events.append(event)
    if isinstance(resolution_or_bpm_events_or_None, int):
        # Using BPMEvent.ParsedData.
        # In this case, BPMEvents must already be in increasing tick order, by definition.
        return BPMEvents(events=events, resolution=Ticks(resolution_or_bpm_events_or_None))
    elif resolution_or_bpm_events_or_None is None:
        # Using AnchorEvent.ParsedData.
        # In this case, AnchorEvents must already be in increasing tick order, by definition.
        return events
    elif isinstance(resolution_or_bpm_events_or_None, BPMEvents):
        # TODO: Should we instead optionally validate a chart, which allows us to assume everything
        # is sorted? etc.
        # NOTE: This `ignore` is because it doesn't understand that e.tick is comparable. When this
        # function is annotated, this can go away.
        return sorted(events, key=lambda e: e.tick)  # type: ignore
    else:  # pragma: no cover
        raise UnreachableError("resolution_or_bpm_events_or_None must be one of the named types")
