from __future__ import annotations

from collections.abc import Callable, Iterator, Sequence
from typing import Any, Generic, Optional, TypeVar, Union, overload

from chartparse.hints import CT, T


class ImmutableList(Sequence[T]):
    def __init__(self, xs: Sequence[T]):
        self._seq = xs

    @overload
    def __getitem__(self, index: int) -> T:
        ...

    @overload
    def __getitem__(self, index: slice) -> Sequence[T]:
        ...

    def __getitem__(self, index: Union[int, slice]) -> Union[T, Sequence[T]]:
        return self._seq[index]

    def __iter__(self) -> Iterator[T]:
        return iter(self._seq)

    def __repr__(self) -> str:  # pragma: no cover
        return repr(self._seq)

    def __len__(self) -> int:
        return len(self._seq)

    def __contains__(self, obj: object) -> bool:
        return obj in self._seq

    def __reversed__(self) -> Iterator[T]:
        return reversed(self._seq)

    def __eq__(self, other: object) -> bool:
        if type(other) is list:
            return self._seq == other
        elif isinstance(other, ImmutableList):
            return self._seq == other._seq
        return NotImplemented


# TODO: Does this class actually need to inherit from Sequence[T]?
class ImmutableSortedList(ImmutableList[T]):
    @overload
    def __init__(self, xs: Sequence[CT]):
        ...

    @overload
    def __init__(self, xs: Sequence[T], key: Callable[[T], CT]):
        ...

    def __init__(self, xs, key=None):
        if key is None:
            super().__init__(list(sorted(xs)))
        else:
            super().__init__(list(sorted(xs, key=key)))
