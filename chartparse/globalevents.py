import re

from chartparse.event import Event
from chartparse.exceptions import RegexFatalNotMatchError
from chartparse.track import _parse_events_from_iterable
from chartparse.util import DictPropertiesEqMixin


class GlobalEventsTrack(DictPropertiesEqMixin):
    def __init__(self, iterator_getter):
        self.text_events = _parse_events_from_iterable(
            iterator_getter(), TextEvent.from_chart_line
        )
        self.section_events = _parse_events_from_iterable(
            iterator_getter(), SectionEvent.from_chart_line
        )
        self.lyric_events = _parse_events_from_iterable(
            iterator_getter(), LyricEvent.from_chart_line
        )


# TODO: Rename to _GlobalEvent.
class GlobalEvent(Event):
    # Match 1: Tick
    # Match 2: Event value (to be added by subclass via template hole)
    _regex_template = r"^\s*?(\d+?) = E \"{}\"\s*?$"

    def __init__(self, tick, value, timestamp=None):
        super().__init__(tick, timestamp=timestamp)
        self.value = value

    @classmethod
    def from_chart_line(cls, line):
        if not hasattr(cls, "_regex_prog"):
            raise NotImplementedError(
                f"{cls.__name__} does not have a _regex_prog value. Perhaps you are trying to "
                "instantiate a GlobalEvent value, rather than one of its implementing subclasses?"
            )

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
    _regex = GlobalEvent._regex_template.format("([^ ]*?)")
    _regex_prog = re.compile(_regex)


class SectionEvent(GlobalEvent):
    _regex = GlobalEvent._regex_template.format("section (.*?)")
    _regex_prog = re.compile(_regex)


class LyricEvent(GlobalEvent):
    _regex = GlobalEvent._regex_template.format("lyric (.*?)")
    _regex_prog = re.compile(_regex)
