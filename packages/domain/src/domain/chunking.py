import re
from dataclasses import dataclass

CHUNK_SIZE = 800
CHUNK_OVERLAP = 100


@dataclass(frozen=True)
class TextSegment:
    text: str
    anchor_start: int
    anchor_end: int


def estimate_token_count(text: str) -> int:
    return max(1, len(text.split()))


def chunk_text(
    text: str, *, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP
) -> list[TextSegment]:
    if not text.strip():
        return []

    segments: list[TextSegment] = []
    start = 0
    length = len(text)

    while start < length:
        end = min(start + chunk_size, length)
        if end < length:
            boundary = text.rfind("\n\n", start, end)
            if boundary > start + chunk_size // 2:
                end = boundary
        segment_text = text[start:end].strip()
        if segment_text:
            segments.append(TextSegment(text=segment_text, anchor_start=start, anchor_end=end))
        if end >= length:
            break
        start = max(end - overlap, start + 1)

    return segments


def chunk_markdown(text: str) -> list[TextSegment]:
    sections = re.split(r"(?=^#{1,3}\s)", text, flags=re.MULTILINE)
    segments: list[TextSegment] = []
    offset = 0
    for section in sections:
        if not section.strip():
            offset += len(section)
            continue
        for part in chunk_text(section):
            segments.append(
                TextSegment(
                    text=part.text,
                    anchor_start=offset + part.anchor_start,
                    anchor_end=offset + part.anchor_end,
                )
            )
        offset += len(section)
    return segments if segments else chunk_text(text)
