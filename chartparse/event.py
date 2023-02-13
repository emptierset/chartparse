"""For functionality useful for all event objects.

.. _Google Python Style Guide:
    http://google.github.io/styleguide/pyguide.html

"""

from __future__ import annotations

import abc
import dataclasses
import typing as typ

from chartparse.time import Timestamp
from chartparse.util import DictPropertiesEqMixin, DictReprMixin

if typ.TYPE_CHECKING:  # pragma: no cover
    from chartparse.tick import Tick


@dataclasses.dataclass(kw_only=True, frozen=True)
class Event(DictPropertiesEqMixin, DictReprMixin):
    """An event that occurs at a tick and timestamp in an event track.

    This is typically used only as a base class for more specialized subclasses. It implements an
    attractive ``__str__`` representation.

    This is a ``frozen``, ``kw_only`` dataclass.
    """

    tick: Tick
    """The tick at which this event occurs."""

    timestamp: Timestamp
    """The timestamp when this event occurs."""

    _proximal_bpm_event_index: int = 0

    # TODO: Figure out a way for the final closing parenthesis to wrap _around_ any additional info
    # added by subclass __str__ implementations.
    def __str__(self) -> str:
        to_join = [f"{type(self).__name__}(t@{self.tick:07})"]
        as_str = (
            str(self.timestamp)
            # This normally converts to str with six decimal digits, but for integral timedeltas,
            # it prints with no decimal places. Manually force decimals to be included so
            # everything lines up prettily.
            if not self.timestamp.total_seconds().is_integer()
            else f"{self.timestamp}.000000"
        )
        to_join.append(f": {as_str}")
        return "".join(to_join)

    @dataclasses.dataclass(kw_only=True, frozen=True)
    class ParsedData(abc.ABC):
        """The data on a single chart line associated with an ``Event``.

        This is a ``frozen``, ``kw_only`` dataclass.
        """

        tick: Tick
        """The tick at which the event represented by this data occurs."""

        _Self = typ.TypeVar("_Self", bound="Event.ParsedData")

        @classmethod
        @abc.abstractmethod
        def from_chart_line(cls: type[_Self], line: str) -> _Self:
            ...  # pragma: no cover
