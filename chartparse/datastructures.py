"""For abstract data structures.

.. _Google Python Style Guide:
    http://google.github.io/styleguide/pyguide.html

"""

from __future__ import annotations

import bisect
import typing
from collections.abc import Callable, Iterable, Iterator, Sequence
from typing import Literal, Union

from chartparse.exceptions import ProgrammerError
from chartparse.hints import ComparableT, T_co


class ImmutableList(Sequence[T_co]):
    """A ``list`` equivalent that cannot be mutated.

    .. automethod:: __getitem__
    .. automethod:: __iter__
    .. automethod:: __repr__
    .. automethod:: __len__
    .. automethod:: __contains__
    .. automethod:: __reversed__
    .. automethod:: __eq__
    """

    # This is conceptually Final, but annotating it as such causes a mypy error due to the type
    # variable.
    _seq: Sequence[T_co]

    length: int

    def __init__(self, xs: Iterable[T_co]):
        if isinstance(xs, Sequence):
            self._seq = xs
            self.length = len(xs)
        else:
            self._seq = list(xs)
            self.length = len(self._seq)

    @typing.overload
    def __getitem__(self, index: int) -> T_co:
        ...  # pragma: no cover

    @typing.overload
    def __getitem__(self, index: slice) -> Sequence[T_co]:
        ...  # pragma: no cover

    def __getitem__(self, index: Union[int, slice]) -> Union[T_co, Sequence[T_co]]:
        return self._seq[index]

    def __iter__(self) -> Iterator[T_co]:
        return iter(self._seq)

    def __repr__(self) -> str:
        return repr(self._seq)  # pragma: no cover

    def __len__(self) -> int:
        return self.length

    def __contains__(self, obj: object) -> bool:
        return obj in self._seq

    def __reversed__(self) -> Iterator[T_co]:
        return reversed(self._seq)

    def __eq__(self, other: object) -> bool:
        if type(other) is list:
            return self._seq == other
        elif isinstance(other, ImmutableList):
            return self._seq == other._seq
        return NotImplemented


@typing.final
class ImmutableSortedList(ImmutableList[T_co]):
    """A ``list`` equivalent that cannot be mutated and is sorted during initialization."""

    @typing.overload
    def __init__(self, xs: Iterable[ComparableT]) -> None:
        ...  # pragma: no cover

    @typing.overload
    def __init__(self, xs: Iterable[ComparableT], *, already_sorted: bool) -> None:
        ...  # pragma: no cover

    @typing.overload
    def __init__(self, xs: Iterable[T_co], *, already_sorted: Literal[True]) -> None:
        ...  # pragma: no cover

    @typing.overload
    def __init__(self, xs: Iterable[T_co], *, key: Callable[[T_co], ComparableT]) -> None:
        ...  # pragma: no cover

    def __init__(self, xs, *, key=None, already_sorted=False) -> None:
        if already_sorted:  # covers sigs 2 and 3
            super().__init__(xs)
        elif key is None:  # covers sig 1
            super().__init__(sorted(xs))
        elif key is not None:  # covers sig 4
            super().__init__(sorted(xs, key=key))
        else:  # pragma: no cover
            raise ProgrammerError

    def binary_search(self, x, *, lo=0, hi=None, key=None):
        if hi is None:
            hi = self.length
        index = bisect.bisect_left(self._seq, x, lo=lo, hi=hi, key=key)
        if index == hi or self._seq[index] != x:
            return None
        return index

    def find_le(self, x, *, lo=0, hi=None, key=None):
        index = bisect.bisect_right(self._seq, x, lo=lo, hi=hi, key=key)
        if index:
            return index - 1
        raise ValueError(f"query value {x} less than all list elements")


# TODO: ImmutableSortedUniqueList, for bpm events. Requires a key parameter, since the values might
# be unique under some transformation (`lambda e: e.tick` for bpm events).
