# TODO: Rename to `events.py`

from chartparse.exceptions import RegexFatalNotMatchError
from chartparse.util import DictPropertiesEqMixin, DictReprMixin


class FromChartLineMixin(object):
    """Mixes in a method to parse an :class:`~chartparse.event.Event` object from a chart line."""

    # TODO: Rename to `from_string`.
    @classmethod
    def from_chart_line(cls, line):
        """Attempt to obtain an instance of this object from a string.

        Args:
            line (str): A string. Most likely a line from a Moonscraper ``.chart``.

        Returns:
            An an instance of this object parsed from ``line``.

        Raises:
            NotImplementedError: If the mixed-into class does not define a ``_regex_prog``
                attribute.
            RegexFatalNotMatchError: If the mixed-into class' ``_regex`` does not match ``line``.
        """

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
    """An event that occurs at a specific tick in an :class:`~chartparse.track.EventTrack`.

    This is typically used only as a base class for more specialized subclasses. It implements an
    attractive ``__str__`` representation.

    Attributes:
        tick (int): The tick at which this event occurs.
        timestamp (datetime.timedelta, optional): The timestamp at which this event occurs.
            Optional because it may need to be calculated later.
    """

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
