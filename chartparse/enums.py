from __future__ import annotations

import enum

from chartparse.hints import T


class AllValuesGettableEnum(enum.Enum):
    """A wrapper for ``Enum`` that adds a method for returning all enum values."""

    # TODO: Return an ImmutableList instead. This is an abuse of tuples.
    @classmethod
    def all_values(cls) -> tuple[T, ...]:
        """Returns a tuple containing all Enum values.

        Returns:
            A tuple containing all Enum values.
        """
        return tuple(c.value for c in cls)
