"""For custom exceptions raised in this package.

.. _Google Python Style Guide:
    http://google.github.io/styleguide/pyguide.html

"""

from __future__ import annotations

import typing as typ

if typ.TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Collection


def raise_(ex: Exception) -> None:
    """Raises ``ex``.

    Can be used to raise an exception from within a lambda.
    """

    raise ex


@typ.final
class MissingRequiredField(Exception):
    """Raised when a required :class:`~chartparse.metadata.Metadata` could not be parsed."""

    field_name: typ.Final[str]
    message: typ.Final[str]

    def __init__(self, field_name: str) -> None:
        self.field_name = field_name
        self.message = f"unable to find a chart line matching required field '{field_name}'"
        super().__init__(self.message)


@typ.final
class RegexNotMatchError(Exception):
    """Raised when a regex failed to match."""

    regex: typ.Final[str]
    message: typ.Final[str]

    @typ.overload
    def __init__(self, regex: str) -> None:
        ...  # pragma: no cover

    @typ.overload
    def __init__(self, regex: str, s: str) -> None:
        ...  # pragma: no cover

    @typ.overload
    def __init__(self, regex: str, s: Collection[str]) -> None:
        ...  # pragma: no cover

    def __init__(self, regex: str, s: typ.Union[None, str, Collection[str]] = None) -> None:
        if s is None:
            message = f"regex '{regex}' failed to match"
        elif isinstance(s, str):
            message = f"string '{s}' failed to match regex '{regex}'"
        else:
            message = f"none of {len(s)} strings matched regex '{regex}'"
        super().__init__(message)
        self.regex = regex
        self.message = message


@typ.final
class ProgrammerError(Exception):
    """Raised in branches that should be unreachable.

    Oftentimes, these branches must exist to satisfy mypy. If this error is raised, it indicates
    a fundamental issue with the code that should have been caught during review.
    """

    message: typ.Final[str] = "should be impossible"

    def __init__(self) -> None:
        super().__init__(self.message)
