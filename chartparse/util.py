from enum import Enum


# TODO: Move to enums.py.
class AllValuesGettableEnum(Enum):
    """A wrapper for ``Enum`` that adds a method for returning all enum values."""

    @classmethod
    def all_values(cls):
        """Returns a tuple containing all Enum values.

        Returns:
            A tuple containing all Enum values.
        """
        return tuple(map(lambda c: c.value, cls))


class DictPropertiesEqMixin(object):
    """A mixin that implements ``__eq__`` via ``__dict__().__eq__``."""

    def __eq__(self, other):
        if not issubclass(other.__class__, DictPropertiesEqMixin):
            raise NotImplementedError(
                (
                    f"cannot equate values of type {self.__class__.__name__} and "
                    f"{other.__class__.__name__}"
                )
            )
        return self.__dict__ == other.__dict__


class DictReprMixin(object):
    """A mixin that implements ``__repr__`` by dumping ``__dict__()``."""

    def __repr__(self):  # pragma: no cover
        return f"{type(self).__name__}({self.__dict__})"


# TODO: Move this to chart.py and make it private.
def iterate_from_second_elem(xs):
    """Given an iterable xs, return an iterator that skips xs[0].

    Args:
        xs (iterable): Any non-exhausted iterable.

    Returns:
        A iterator that iterates over xs, ignoring the first element.
    """
    it = iter(xs)
    next(it)
    yield from it
