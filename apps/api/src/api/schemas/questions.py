from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class QuestionBody(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    mode: str = "hybrid"
    limit: int = Field(default=12, ge=1, le=30)


class CitationResponse(BaseModel):
    citation_id: str
    chunk_id: UUID | None = None
    source_id: UUID | None = None
    external_id: str | None = None
    excerpt: str
    score: float
    signal: str


class AnswerClaimResponse(BaseModel):
    text: str
    confidence: float
    citation_ids: list[str]


class RetrievalStepResponse(BaseModel):
    signal: str
    description: str
    result_count: int


class QuestionAnswerResponse(BaseModel):
    question: str
    answer: str
    confidence: float
    insufficient_evidence: bool
    citations: list[CitationResponse]
    claims: list[AnswerClaimResponse]
    related_entity_ids: list[UUID]
    retrieval_plan: list[RetrievalStepResponse]
    model: str | None = None
    created_at: datetime
