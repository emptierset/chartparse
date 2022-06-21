# TODO: Rename to `events.py`

from chartparse.exceptions import RegexFatalNotMatchError
from chartparse.util import DictPropertiesEqMixin, DictReprMixin


class FromChartLineMixin(object):
    @classmethod
    def from_chart_line(cls, line):
        if not hasattr(cls, "_regex_prog"):
            raise NotImplementedError(
                f"{cls.__name__} does not have a _regex_prog value. Perhaps you are trying to "
                "instantiate a {cls.__bases__[0].__name__} value, rather than one of its "
                "implementing subclasses?"
            )

        m = cls._regex_prog.match(line)
        if not m:
            raise RegexFatalNotMatchError(cls._regex, line)
        tick, value = int(m.group(1)), m.group(2)
        return cls(tick, value)


class Event(DictPropertiesEqMixin, DictReprMixin):
    def __init__(self, tick, timestamp=None):
        self.tick = tick
        self.timestamp = timestamp

    def __str__(self):  # pragma: no cover
        to_join = [f"{type(self).__name__: >18}(t@{self.tick:07}"]
        if self.timestamp is not None:
            as_str = (
                str(self.timestamp)
                if self.timestamp.total_seconds() > 0
                else f"{self.timestamp}.000000"
            )
            to_join.append(f" {as_str}")
        to_join.append(")")
        return "".join(to_join)


class SustainedEvent(Event, FromChartLineMixin):
    def __init__(self, tick, sustain, timestamp=None):
        super().__init__(tick, timestamp=timestamp)
        self.sustain = sustain

    @classmethod
    def from_chart_line(cls, line):
        event = super().from_chart_line(line)
        event.sustain = int(event.sustain)
        return event

    def __str__(self):  # pragma: no cover
        to_join = [super().__str__()]
        to_join.append(f": sustain={self.sustain}")
        return "".join(to_join)
