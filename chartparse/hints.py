"""For type annotation related utilities.

.. _Google Python Style Guide:
    http://google.github.io/styleguide/pyguide.html

"""

from __future__ import annotations

import typing as typ
from abc import abstractmethod


@typ.runtime_checkable
class Comparable(typ.Protocol):
    """Protocol for annotating comparable types."""

    @abstractmethod
    def __lt__(self, other: typ.Any) -> bool:
        ...  # pragma: no cover


T = typ.TypeVar("T")
T_co = typ.TypeVar("T_co", covariant=True)

ComparableT = typ.TypeVar("ComparableT", bound=Comparable)
"""A type for comparable values."""
