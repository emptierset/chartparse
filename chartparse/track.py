"""For functionality useful for all event track objects.

Most notably, :class:`~chartparse.instrument.InstrumentTrack`, :class:`~chartparse.sync.SyncTrack`,
and :class:`~chartparse.globalevents.GlobalEventsTrack` are considered to be event tracks.

.. _Google Python Style Guide:
    http://google.github.io/styleguide/pyguide.html

"""

from __future__ import annotations

import typing
from collections.abc import Callable, Iterable
from typing import Optional, Union

from chartparse.datastructures import ImmutableSortedList
from chartparse.event import EventT, TimestampAtTickSupporter
from chartparse.exceptions import ProgrammerError, RegexNotMatchError
from chartparse.sync import BPMEvent


@typing.overload
def parse_events_from_chart_lines(
    chart_lines: Iterable[str],
    from_chart_line_fn: Callable[[str, Optional[BPMEvent], int], BPMEvent],
    resolution: int,
    /,
) -> ImmutableSortedList[BPMEvent]:
    ...  # pragma: no cover


@typing.overload
def parse_events_from_chart_lines(
    chart_lines: Iterable[str],
    from_chart_line_fn: Callable[[str, Optional[EventT], TimestampAtTickSupporter], EventT],
    tatter: TimestampAtTickSupporter,
    /,
) -> ImmutableSortedList[EventT]:
    ...  # pragma: no cover


def parse_events_from_chart_lines(
    chart_lines: Iterable[str],
    from_chart_line_fn: Union[
        Callable[[str, Optional[BPMEvent], int], BPMEvent],
        Callable[[str, Optional[EventT], TimestampAtTickSupporter], EventT],
    ],
    resolution_or_tatter: Union[int, TimestampAtTickSupporter],
    /,
) -> Union[ImmutableSortedList[BPMEvent], ImmutableSortedList[EventT]]:
    # TODO: figure out how overload works with autodoc.
    """Attempt to obtain a ``Event`` from each element of ``chart_lines``.

    Args:
        chart_lines: An iterable of strings, most likely from a Moonscraper ``.chart``.
        from_chart_line_fn: A function that, when applied to each element of ``chart_lines``,
            either returns a :class:`~chartparse.event.Event` or raises
            :class:`~chartparse.exceptions.RegexNotMatchError`.
        resolution_or_tatter: Either the resolution of the chart, or an object that can be used to
            get a timestamp at a particular tick.

    Returns:
        A :class:`~chartparse.datastructures.ImmutableSortedList` of
        :class:`~chartparse.event.Event` objects obtained by calling ``from_chart_line_fn`` on
        each element of ``chart_lines``.
    """

    # TODO: Create _parse_events_from_chart_line_impl, which takes a Type argument and uses it
    # to narrow the Union types of the other parameters.
    if isinstance(resolution_or_tatter, int):
        resolution = resolution_or_tatter
        from_chart_line_fn = typing.cast(
            Callable[[str, Optional[BPMEvent], int], BPMEvent], from_chart_line_fn
        )
        bpm_events: list[BPMEvent] = []
        for line in chart_lines:
            prev_bpm_event = bpm_events[-1] if bpm_events else None
            assert prev_bpm_event is None or isinstance(prev_bpm_event, BPMEvent)
            try:
                bpm_event = from_chart_line_fn(line, prev_bpm_event, resolution)
            except RegexNotMatchError:
                continue
            bpm_events.append(bpm_event)
        return ImmutableSortedList(bpm_events, key=lambda e: e.tick)
    elif isinstance(resolution_or_tatter, TimestampAtTickSupporter):
        tatter = resolution_or_tatter
        from_chart_line_fn = typing.cast(
            Callable[[str, Optional[EventT], TimestampAtTickSupporter], EventT], from_chart_line_fn
        )
        events: list[EventT] = []
        for line in chart_lines:
            prev_event = events[-1] if events else None
            try:
                event = from_chart_line_fn(line, prev_event, tatter)
            except RegexNotMatchError:
                continue
            events.append(event)
        return ImmutableSortedList(events, key=lambda e: e.tick)
    else:
        raise ProgrammerError  # pragma: no cover
