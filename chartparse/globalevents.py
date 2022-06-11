import re

from chartparse.event import Event
from chartparse.exceptions import RegexFatalNotMatchError
from chartparse.track import _parse_events_from_iterable
from chartparse.util import DictPropertiesEqMixin


class GlobalEventsTrack(DictPropertiesEqMixin):
    def __init__(self, iterator_getter):
        self.events = _parse_events_from_iterable(iterator_getter(), GlobalEvent.from_chart_line)


class GlobalEvent(Event):
    # Match 1: Tick
    # Match 2: Event command
    # Match 3: Event parameters (optional)
    _regex = r"^\s*?(\d+?)\s=\sE\s\"([a-z0-9_]+?)(?:\s(.+?))?\"\s*?$"
    _regex_prog = re.compile(_regex)

    def __init__(self, tick, command, timestamp=None, params=None):
        super().__init__(tick, timestamp=timestamp)
        self.command = command
        self.params = params

    @classmethod
    def from_chart_line(cls, line):
        m = cls._regex_prog.match(line)
        if not m:
            raise RegexFatalNotMatchError(cls._regex, line)
        tick, command, params = int(m.group(1)), m.group(2), m.group(3)
        return cls(tick, command, params=params)

    def __str__(self):  # pragma: no cover
        to_join = [super().__str__()]
        to_join.append(f": {self.command}")
        if self.params:
            to_join.append(f" [params={self.params}]")
        return "".join(to_join)
