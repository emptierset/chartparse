"""For mutating attributes in a type-unsafe manner.

Frozen dataclasses are difficult to test around, since substituting values (via mocking, for
example) runs into FrozenDataclassErrors. These functions allow you to circumvent that. Only use
these in tests.
"""


def setattr(obj, attrname, value):
    object.__setattr__(obj, attrname, value)


def delattr(obj, attrname):
    object.__delattr__(obj, attrname)
