class ParserError(Exception):
    """Raised when document parsing fails for a specific file."""

    def __init__(self, message: str, *, parser_type: str | None = None) -> None:
        self.parser_type = parser_type
        super().__init__(message)
