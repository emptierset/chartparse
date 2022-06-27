class ImmutableList(list):
    def __init__(self, xs):
        self._list = xs

    def __getitem__(self, index):
        return self._list[index]

    def __iter__(self):
        return iter(self._list)

    def __repr__(self):  # pragma: no cover
        return repr(self._list)

    def __len__(self):
        return len(self._list)

    def __eq__(self, other):
        if type(other) is list:
            return self._list == other
        elif isinstance(other, ImmutableList):
            return self._list == other._list
        raise NotImplementedError(
            (
                f"cannot equate values of type {self.__class__.__name__} and "
                f"{other.__class__.__name__}"
            )
        )

    def _NotImplemented(self, *args, **kw):
        raise NotImplementedError(
            f"{self.__class__.__name__} does not implement mutative methods."
        )

    append = _NotImplemented
    pop = _NotImplemented
    __delitem__ = _NotImplemented

    def __setitem__(self, key, value):
        self._NotImplemented()


class ImmutableSortedList(ImmutableList):
    def __init__(self, xs, key=None):
        if key is None:
            key = lambda x: x
        super().__init__(sorted(xs, key=key))
