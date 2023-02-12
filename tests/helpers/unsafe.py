"""For mutating attributes in a type-unsafe manner.

Frozen dataclasses are difficult to test around, since substituting values (via mocking, for
example) runs into FrozenDataclassErrors. These functions allow you to circumvent that. Only use
these in tests.
"""

import typing as typ


def setattr(obj: typ.Any, attrname: str, value: typ.Any) -> None:
    object.__setattr__(obj, attrname, value)


def delattr(obj: typ.Any, attrname: str) -> None:
    object.__delattr__(obj, attrname)
