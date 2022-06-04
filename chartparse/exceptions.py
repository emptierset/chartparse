class RegexFatalNotMatchError(Exception):
    """Exception raised when a regex fatally failed to match."""

    def __init__(self, regex, s):
        self.regex = regex
        self.message = f"string '{s}' fatally failed to match regex '{regex}'"
        super().__init__(self.message)
