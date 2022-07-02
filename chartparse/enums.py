from __future__ import annotations

import enum

from chartparse.datastructures import ImmutableList
from chartparse.hints import T


class AllValuesGettableEnum(enum.Enum):
    """A wrapper for ``Enum`` that adds a method for returning all enum values."""

    @classmethod
    def all_values(cls) -> ImmutableList[T]:
        """Returns all Enum values.

        Returns:
            An :class:`~chartparse.datastructures.ImmutableList` containing all Enum values.
        """
        return ImmutableList([c.value for c in cls])
