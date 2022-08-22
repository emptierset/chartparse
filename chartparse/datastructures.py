"""For abstract data structures.

.. _Google Python Style Guide:
    http://google.github.io/styleguide/pyguide.html

"""

from __future__ import annotations

import typing
from collections.abc import Callable, Iterable, Iterator, Sequence
from typing import Union

from chartparse.hints import ComparableT, T


class ImmutableList(Sequence[T]):
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
    _seq: Sequence[T]

    length: int

    def __init__(self, xs: Iterable[T]):
        if isinstance(xs, Sequence):
            self._seq = xs
            self.length = len(xs)
        else:
            self._seq = list(xs)
            self.length = len(self._seq)

    @typing.overload
    def __getitem__(self, index: int) -> T:
        ...  # pragma: no cover

    @typing.overload
    def __getitem__(self, index: slice) -> Sequence[T]:
        ...  # pragma: no cover

    def __getitem__(self, index: Union[int, slice]) -> Union[T, Sequence[T]]:
        return self._seq[index]

    def __iter__(self) -> Iterator[T]:
        return iter(self._seq)

    def __repr__(self) -> str:
        return repr(self._seq)  # pragma: no cover

    def __len__(self) -> int:
        return self.length

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


# TODO: Allow binary searching?
@typing.final
class ImmutableSortedList(ImmutableList[T]):
    """A ``list`` equivalent that cannot be mutated and is sorted during initialization."""

    @typing.overload
    def __init__(self, xs: Iterable[ComparableT], *, already_sorted: bool = False) -> None:
        ...  # pragma: no cover

    @typing.overload
    def __init__(self, xs: Iterable[T], *, key: Callable[[T], ComparableT]) -> None:
        ...  # pragma: no cover

    def __init__(self, xs, *, key=None, already_sorted=False) -> None:
        if already_sorted:
            super().__init__(xs)
        elif key is None:
            super().__init__(sorted(xs))
        elif key is not None:
            super().__init__(sorted(xs, key=key))
        else:  # pragma: no cover
            raise TypeError
