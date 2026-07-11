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
    llm_available: bool
    extraction: ExtractionResult
    provider: str
    fallback_used: bool
    token_usage: dict[str, object] | None
    llm_error: str | None
    validation_passed: bool
    validation_errors: list[str]
    proposal_count: int
    requires_review_count: int
    error: str | None
