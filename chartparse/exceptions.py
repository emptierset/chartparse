from __future__ import annotations


class RegexNotMatchError(Exception):
    """Raised when a regex failed to match."""

    def __init__(self, regex: str, s: str):
        self.regex = regex
        self.message = f"string '{s}' fatally failed to match regex '{regex}'"
        super().__init__(self.message)
