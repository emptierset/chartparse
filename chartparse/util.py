"""For various utilities useful throughout ``chartparse``.

.. _Google Python Style Guide:
    http://google.github.io/styleguide/pyguide.html

"""

from __future__ import annotations

import enum
from collections.abc import Sequence

from chartparse.hints import T


class DictPropertiesEqMixin(object):
    """A mixin that implements ``__eq__`` via ``__dict__().__eq__``.

    An object with this mixed in will equate to other objects that share this mixin and have equal
    ``__dict__``\\s.
    """

    def __eq__(self, other: object) -> bool:
        if not issubclass(other.__class__, DictPropertiesEqMixin):
            return NotImplemented
        return self.__dict__ == other.__dict__


class DictReprMixin(object):
    """A mixin implementing ``__repr__`` by dumping ``__dict__()``.

    Additionally, this ignores class attributes, since they (typically) do not change and are
    therefore uninteresting.
    """

    def __repr__(self) -> str:
        instance_attrs = {k: v for k, v in self.__dict__.items() if not hasattr(self.__class__, k)}
        return f"{type(self).__name__}({str(instance_attrs)[1:-1]})"


# TODO(P2): this (and DictReprMixin) probably needs to handle missing values somehow? The repr of
# bare test objects raises an exception for missing attributes, but I guess it expects them to be
# there because they are dataclasses?
class DictReprTruncatedSequencesMixin(object):
    """A mixin implementing ``__repr__`` by dumping ``__dict__()`` with truncated sequences.

    Specifically, any instance attribute of type `Sequence
    <https://docs.python.org/3/library/collections.abc.html#collections.abc.Sequence>`_ with
    more than 1 element will be represented as such::

        ["foo", ... 4 more elements]

    Additionally, this ignores class attributes, since they (typically) do not change and are
    therefore uninteresting.
    """

    def __repr__(self) -> str:
        # TODO(P2): This doesn't work if dataclasses were created in the "bare" manner, since it
        # thinks all of the dataclass' fields should be set, and crashes when they aren't. Possible
        # solution is to migrate all usage of "bare" to "minimal".
        instance_attrs = {k: v for k, v in self.__dict__.items() if not hasattr(self.__class__, k)}

        items = []
        for k, v in instance_attrs.items():
            item = f"'{k}': "
            if isinstance(v, Sequence) and len(v) > 1:
                item += f"[{v[0]}, ... {len(v)-1} more elements]"
            else:
                item += f"{v}"
            items.append(item)

        item_string = ", ".join(items)
        return f"{type(self).__name__}({item_string})"


class AllValuesGettableEnum(enum.Enum):
    """A wrapper for ``Enum`` that adds a method for returning all enum values."""

    @classmethod
    def all_values(cls) -> Sequence[T]:
        """Returns all Enum values.

        Returns:
            A Sequence containing all Enum values.
        """
        return [c.value for c in cls]
