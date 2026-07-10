from typing import Protocol

from domain.content import ParsedDocument


class DocumentParser(Protocol):
    def parse(self, content: bytes, mime_type: str | None, external_id: str) -> ParsedDocument: ...
