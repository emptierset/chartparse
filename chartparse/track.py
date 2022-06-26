from chartparse.exceptions import RegexFatalNotMatchError


class EventTrack(object):
    """Mixes in a method for parsing :class:`~chartparse.event.Event` objects from chart lines."""

    # TODO: Rename to _parse_events_from_chart_lines. Plural noun is obviously an iterable.
    @staticmethod
    def _parse_events_from_iterable(iterable, from_chart_line_fn):
        """Attempt to obtain an :class:`~chartparse.event.Event` from each element of ``iterable``.

        Args:
            iterable (list): Any iterable.
            from_chart_line_fn (function): A function that, when applied to each element of
                ``iterable``, either returns a :class:`~chartparse.event.Event` or raises
                :class:`~chartparse.exceptions.RegexFatalNotMatchError`.

        Returns:
            A ``list`` of :class:`~chartparse.event.Event` objects obtained by calling
            ``from_chart_line_fn`` on each element of ``iterable``.
        """

        events = []
        for line in iterable:
            try:
                event = from_chart_line_fn(line)
            except RegexFatalNotMatchError:
                continue
            events.append(event)
        events.sort(key=lambda e: e.tick)
        return events
