from __future__ import annotations


# TODO: Rename to RegexNotMatchError <22-06-2022, Andrew Conant> #
class RegexNotMatchError(Exception):
    """Raised when a regex fatally failed to match."""

    def __init__(self, regex: str, s: str):
        self.regex = regex
        self.message = f"string '{s}' fatally failed to match regex '{regex}'"
        super().__init__(self.message)
