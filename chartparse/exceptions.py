from __future__ import annotations

from typing import Pattern


# TODO: Rename to RegexFatalNotMatchError <22-06-2022, Andrew Conant> #
class RegexFatalNotMatchError(Exception):
    """Exception raised when a regex fatally failed to match."""

    def __init__(self, regex: str, s: str):
        self.regex = regex
        self.message = f"string '{s}' fatally failed to match regex '{regex}'"
        super().__init__(self.message)
