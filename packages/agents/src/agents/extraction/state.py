from typing import TypedDict
from uuid import UUID

from domain.extraction import ExtractionResult


class ExtractionState(TypedDict, total=False):
    version_id: UUID
    owner_id: UUID
    source_id: UUID
    project_id: UUID | None
    correlation_id: str | None
    chunks: list[tuple[UUID, str]]
    full_text: str
    extraction: ExtractionResult
    proposal_count: int
    error: str | None
