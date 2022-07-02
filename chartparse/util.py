from __future__ import annotations


class DictPropertiesEqMixin(object):
    """A mixin that implements ``__eq__`` via ``__dict__().__eq__``."""

    def __eq__(self, other: object) -> bool:
        if not issubclass(other.__class__, DictPropertiesEqMixin):
            return NotImplemented
        return self.__dict__ == other.__dict__


class DictReprMixin(object):
    """A mixin that implements ``__repr__`` by dumping ``__dict__()``."""

    def __repr__(self) -> str:  # pragma: no cover
        return f"{type(self).__name__}({self.__dict__})"
