from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import ClassVar

from chartparse.datastructures import ImmutableSortedList
from chartparse.event import EventT
from chartparse.exceptions import RegexFatalNotMatchError


class EventTrack(object):
    """Mixes in a method for parsing ``Event`` objects from chart lines."""

    # TODO: Rename to _parse_events_from_chart_lines. Plural noun is obviously an iterable.
    @staticmethod
    def _parse_events_from_iterable(
        chart_lines: Iterable[str], from_chart_line_fn: Callable[[str], EventT]
    ) -> ImmutableSortedList[EventT]:
        """Attempt to obtain an ``Event`` from each element of ``chart_lines``.

        Args:
            chart_lines: An iterable of strings, most likely from a Moonscraper ``.chart``.
            from_chart_line_fn: A function that, when applied to each element of ``chart_lines``,
                either returns a :class:`~chartparse.event.Event` or raises
                :class:`~chartparse.exceptions.RegexFatalNotMatchError`.

        Returns:
            A :class:`~chartparse.datastructures.ImmutableSortedList` of
            :class:`~chartparse.event.Event` objects obtained by calling ``from_chart_line_fn`` on
            each element of ``chart_lines``.
        """

        events = []
        for line in chart_lines:
            try:
                event = from_chart_line_fn(line)
            except RegexFatalNotMatchError:
                continue
            events.append(event)
        return ImmutableSortedList(events, key=lambda e: e.tick)


class HasSectionNameMixin(object):
    """A part of a ``.chart`` file that has a specific, always-the-same name."""

    section_name: ClassVar[str]
    """The name of this track's section in a ``.chart`` file."""
