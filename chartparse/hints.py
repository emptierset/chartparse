from __future__ import annotations

from abc import abstractmethod
from collections.abc import Sequence
from typing import Any, Protocol, TypeVar

from typing_extensions import TypeGuard


class Comparable(Protocol):
    """Protocol for annotating comparable types."""

    @abstractmethod
    def __lt__(self, other: Any) -> bool:
        ...


T = TypeVar("T")
CT = TypeVar("CT", bound=Comparable)
