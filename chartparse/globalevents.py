import re

from chartparse.event import Event, FromChartLineMixin
from chartparse.track import EventTrack
from chartparse.util import DictPropertiesEqMixin


class GlobalEventsTrack(EventTrack, DictPropertiesEqMixin):
    def __init__(self, text_events, section_events, lyric_events):
        self.text_events = text_events
        self.section_events = section_events
        self.lyric_events = lyric_events

    @classmethod
    def from_chart_lines(cls, iterator_getter):
        text_events = cls._parse_events_from_iterable(iterator_getter(), TextEvent.from_chart_line)
        section_events = cls._parse_events_from_iterable(
            iterator_getter(), SectionEvent.from_chart_line
        )
        lyric_events = cls._parse_events_from_iterable(
            iterator_getter(), LyricEvent.from_chart_line
        )
        return cls(text_events, section_events, lyric_events)


class _GlobalEvent(Event, FromChartLineMixin):
    # Match 1: Tick
    # Match 2: Event value (to be added by subclass via template hole)
    _regex_template = r"^\s*?(\d+?) = E \"{}\"\s*?$"

    def __init__(self, tick, value, timestamp=None):
        super().__init__(tick, timestamp=timestamp)
        self.value = value

    def __str__(self):  # pragma: no cover
        to_join = [super().__str__()]
        to_join.append(f": {self.value}")
        return "".join(to_join)


class TextEvent(_GlobalEvent):
    _regex = _GlobalEvent._regex_template.format("([^ ]*?)")
    _regex_prog = re.compile(_regex)


class SectionEvent(_GlobalEvent):
    _regex = _GlobalEvent._regex_template.format("section (.*?)")
    _regex_prog = re.compile(_regex)


class LyricEvent(_GlobalEvent):
    _regex = _GlobalEvent._regex_template.format("lyric (.*?)")
    _regex_prog = re.compile(_regex)
