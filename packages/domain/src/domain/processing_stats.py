from uuid import UUID

from pydantic import BaseModel, Field


class ProcessingErrorSample(BaseModel):
    external_id: str
    error: str


class SourceProcessingStats(BaseModel):
    source_id: UUID
    extraction_pending: int = 0
    extraction_completed: int = 0
    extraction_failed: int = 0
    extraction_skipped: int = 0
    knowledge_pending: int = 0
    knowledge_completed: int = 0
    knowledge_failed: int = 0
    knowledge_skipped: int = 0
    content_chunks: int = 0
    recent_extraction_errors: list[ProcessingErrorSample] = Field(default_factory=list)
