from uuid import UUID

from pydantic import BaseModel


class ProcessingErrorSampleResponse(BaseModel):
    external_id: str
    error: str


class TriageSampleResponse(BaseModel):
    external_id: str
    sensitivity: str
    relevance: float
    review_risk: str
    extractor_hint: str


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
    triage_pending: int
    triage_completed: int
    content_chunks: int
    recent_extraction_errors: list[ProcessingErrorSampleResponse]
    recent_triage_samples: list[TriageSampleResponse]
