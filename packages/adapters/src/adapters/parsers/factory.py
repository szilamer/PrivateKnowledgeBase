from domain.content import ParsedDocument, ParserType


class TextParser:
    PARSER_VERSION = "0.1.0"

    def parse(self, content: bytes, mime_type: str | None, external_id: str) -> ParsedDocument:
        _ = mime_type, external_id
        return ParsedDocument(
            text=content.decode("utf-8", errors="replace"),
            parser_type=ParserType.TEXT,
            parser_version=self.PARSER_VERSION,
        )


class MarkdownParser:
    PARSER_VERSION = "0.1.0"

    def parse(self, content: bytes, mime_type: str | None, external_id: str) -> ParsedDocument:
        _ = mime_type, external_id
        return ParsedDocument(
            text=content.decode("utf-8", errors="replace"),
            parser_type=ParserType.MARKDOWN,
            parser_version=self.PARSER_VERSION,
        )


class PdfParser:
    PARSER_VERSION = "0.1.0"

    def parse(self, content: bytes, mime_type: str | None, external_id: str) -> ParsedDocument:
        _ = mime_type, external_id
        from io import BytesIO

        from pypdf import PdfReader

        reader = PdfReader(BytesIO(content))
        pages = [page.extract_text() or "" for page in reader.pages]
        return ParsedDocument(
            text="\n\n".join(pages).strip(),
            parser_type=ParserType.PDF,
            parser_version=self.PARSER_VERSION,
        )


class ParserFactory:
    def __init__(self) -> None:
        self._text = TextParser()
        self._markdown = MarkdownParser()
        self._pdf = PdfParser()

    def parse(self, content: bytes, mime_type: str | None, external_id: str) -> ParsedDocument:
        lower = external_id.lower()
        if mime_type in {"message/rfc822", "text/email"} or lower.startswith("email:"):
            return self._text.parse(content, mime_type, external_id)
        if mime_type == "text/calendar" or "calendar_event" in lower:
            return self._text.parse(content, mime_type, external_id)
        if lower.endswith(".pdf") or mime_type == "application/pdf":
            return self._pdf.parse(content, mime_type, external_id)
        if lower.endswith(".md") or lower.endswith(".markdown"):
            return self._markdown.parse(content, mime_type, external_id)
        return self._text.parse(content, mime_type, external_id)
