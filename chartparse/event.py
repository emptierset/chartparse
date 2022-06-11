# TODO: Rename to `events.py`

from chartparse.util import DictPropertiesEqMixin, DictReprMixin


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


class DurationedEvent(Event):
    def __init__(self, tick, duration, timestamp=None):
        super().__init__(tick, timestamp=timestamp)
        self.duration = duration

    def __str__(self):  # pragma: no cover
        to_join = [super().__str__()]
        to_join.append(f": duration={self.duration}")
        return "".join(to_join)
