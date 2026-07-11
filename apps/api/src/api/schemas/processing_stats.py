from uuid import UUID

from pydantic import BaseModel


class ProcessingErrorSampleResponse(BaseModel):
    external_id: str
    error: str


class SourceProcessingStatsResponse(BaseModel):
    source_id: UUID
    extraction_pending: int
    extraction_completed: int
    extraction_failed: int
    extraction_skipped: int
    knowledge_pending: int
    knowledge_completed: int
    knowledge_failed: int
    knowledge_skipped: int
    content_chunks: int
    recent_extraction_errors: list[ProcessingErrorSampleResponse]
