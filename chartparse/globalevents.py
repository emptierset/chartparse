import re

from chartparse.event import Event
from chartparse.exceptions import RegexFatalNotMatchError
from chartparse.track import EventTrack
from chartparse.util import DictPropertiesEqMixin


class GlobalEventsTrack(EventTrack, DictPropertiesEqMixin):
    r"""All of a :class:`~chartparse.chart.Chart`'s :class:`~chartparse.globalevents.GlobalEvent`\s.

    Attributes:
        text_events (ImmutableSortedList[TextEvent]): A :class:`~chartparse.chart.Chart` object's
            :class:`~chartparse.globalevents.TextEvent` objects.
        section_events (ImmutableSortedList[SectionEvent]): A :class:`~chartparse.chart.Chart`
            object's :class:`~chartparse.globalevents.SectionEvent` objects.
        lyric_events (ImmutableSortedList[LyricEvent]): A :class:`~chartparse.chart.Chart` object's
            :class:`~chartparse.globalevents.LyricEvent` objects.
    """

    def __init__(self, text_events, section_events, lyric_events):
        """Instantiates all instance attributes.

        Args:
            text_events (ImmutableSortedList[TextEvent]): A :class:`~chartparse.chart.Chart`
                object's :class:`~chartparse.globalevents.TextEvent` objects.
            section_events (ImmutableSortedList[SectionEvent]): A :class:`~chartparse.chart.Chart`
                object's :class:`~chartparse.globalevents.SectionEvent` objects.
            lyric_events (ImmutableSortedList[LyricEvent]): A :class:`~chartparse.chart.Chart`
                object's :class:`~chartparse.globalevents.LyricEvent` objects.
        """

        self.text_events = text_events
        self.section_events = section_events
        self.lyric_events = lyric_events

    @classmethod
    def from_chart_lines(cls, iterator_getter):
        """Initializes instance attributes by parsing an iterable of strings.

        Args:
            iterator_getter (function): A function that returns an iterator over a series of
                strings, most likely from a Moonscraper ``.chart``. Must be a function so the
                strings could be iterated over multiple times, if necessary.

        Returns:
            A ``GlobalEventsTrack`` parsed from the strings returned by ``iterator_getter``.
        """

        text_events = cls._parse_events_from_iterable(iterator_getter(), TextEvent.from_chart_line)
        section_events = cls._parse_events_from_iterable(
            iterator_getter(), SectionEvent.from_chart_line
        )
        lyric_events = cls._parse_events_from_iterable(
            iterator_getter(), LyricEvent.from_chart_line
        )
        return cls(text_events, section_events, lyric_events)


class GlobalEvent(Event):
    """An event in a :class:`~chartparse.globalevents.GlobalEventsTrack`.

    This is typically used only as a base class for more specialized subclasses. It implements an
    attractive ``__str__`` representation and supplies a regular expression template for subclasses
    to fill in.

    Subclasses should define ``_regex_prog`` and can be instantiated with their ``from_chart_line``
    method.

    Attributes:
        value (str): The data that this event stores.
    """

    # Match 1: Tick
    # Match 2: Event value (to be added by subclass via template hole)
    _regex_template = r"^\s*?(\d+?) = E \"{}\"\s*?$"

    def __init__(self, tick, value, timestamp=None):
        super().__init__(tick, timestamp=timestamp)
        self.value = value

    @classmethod
    def from_chart_line(cls, line):
        """Attempt to obtain an instance of this object from a string.

        Args:
            line (str): A string. Most likely a line from a Moonscraper ``.chart``.

        Returns:
            An an instance of this object parsed from ``line``.

        Raises:
            RegexFatalNotMatchError: If the mixed-into class' ``_regex`` does not match ``line``.
        """

        m = cls._regex_prog.match(line)
        if not m:
            raise RegexFatalNotMatchError(cls._regex, line)
        tick, value = int(m.group(1)), m.group(2)
        return cls(tick, value)

    def __str__(self):  # pragma: no cover
        to_join = [super().__str__()]
        to_join.append(f": {self.value}")
        return "".join(to_join)


class TextEvent(GlobalEvent):
    """A :class:`~chartparse.globalevents.GlobalEvent` that stores freeform text event data."""

    _regex = GlobalEvent._regex_template.format("([^ ]*?)")
    _regex_prog = re.compile(_regex)


class SectionEvent(GlobalEvent):
    """A :class:`~chartparse.globalevents.GlobalEvent` that signifies a new section.

    The event's ``value`` attribute contains the section's name.
    """

    _regex = GlobalEvent._regex_template.format("section (.*?)")
    _regex_prog = re.compile(_regex)


class LyricEvent(GlobalEvent):
    """A :class:`~chartparse.globalevents.GlobalEvent` that signifies a new section.

    The event's ``value`` attribute contains the lyric's text, typically a single syllable's worth.
    """

    _regex = GlobalEvent._regex_template.format("lyric (.*?)")
    _regex_prog = re.compile(_regex)
