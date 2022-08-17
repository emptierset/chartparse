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
from chartparse.event import EventT, TimestampGetterT
from chartparse.exceptions import ProgrammerError, RegexNotMatchError
from chartparse.sync import BPMEvent


@typing.overload
def parse_events_from_chart_lines(
    resolution: int,
    chart_lines: Iterable[str],
    from_chart_line_fn: Callable[[str, Optional[BPMEvent], int], BPMEvent],
) -> ImmutableSortedList[BPMEvent]:
    ...  # pragma: no cover


@typing.overload
def parse_events_from_chart_lines(
    resolution: int,
    chart_lines: Iterable[str],
    from_chart_line_fn: Callable[
        [str, Optional[EventT], TimestampGetterT, int],
        EventT,
    ],
    timestamp_getter: TimestampGetterT,
) -> ImmutableSortedList[EventT]:
    ...  # pragma: no cover


def parse_events_from_chart_lines(
    resolution: int,
    chart_lines: Iterable[str],
    from_chart_line_fn: Union[
        Callable[[str, Optional[EventT], TimestampGetterT, int], EventT],
        Callable[[str, Optional[BPMEvent], int], BPMEvent],
    ],
    timestamp_getter: Optional[TimestampGetterT] = None,
) -> Union[ImmutableSortedList[BPMEvent], ImmutableSortedList[EventT]]:
    """Attempt to obtain a ``Event`` from each element of ``chart_lines``.

    Args:
        chart_lines: An iterable of strings, most likely from a Moonscraper ``.chart``.
        from_chart_line_fn: A function that, when applied to each element of ``chart_lines``,
            either returns a :class:`~chartparse.event.Event` or raises
            :class:`~chartparse.exceptions.RegexNotMatchError`.
        timestamp_getter: A callable that can be used to obtain a timestamp at a given tick and
            resolution.
        resolution: The resolution of the chart.

    Returns:
        A :class:`~chartparse.datastructures.ImmutableSortedList` of
        :class:`~chartparse.event.Event` objects obtained by calling ``from_chart_line_fn`` on
        each element of ``chart_lines``.
    """

    events = []  # type: ignore
    for line in chart_lines:
        prev_event = events[-1] if events else None
        try:
            if timestamp_getter is None:
                assert prev_event is None or isinstance(prev_event, BPMEvent)
                from_chart_line_fn = typing.cast(
                    Callable[[str, Optional[BPMEvent], int], BPMEvent], from_chart_line_fn
                )
                typing.cast(list[BPMEvent], events).append(
                    from_chart_line_fn(line, prev_event, resolution)
                )
            elif timestamp_getter is not None:
                from_chart_line_fn = typing.cast(
                    Callable[
                        [str, Optional[EventT], TimestampGetterT, int],
                        EventT,
                    ],
                    from_chart_line_fn,
                )
                typing.cast(list[EventT], events).append(
                    from_chart_line_fn(line, prev_event, timestamp_getter, resolution)
                )
            else:
                raise ProgrammerError  # pragma: no cover
        except RegexNotMatchError:
            continue
    # TODO: We don't actually need to sort lists of Events if we
    # have to assume that they are in increasing tick order. Maybe add an
    # "already_sorted" optimization flag to the constructor?
    return ImmutableSortedList(events, key=lambda e: e.tick)
