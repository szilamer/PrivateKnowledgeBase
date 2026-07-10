from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field


class RetrievalSignal(StrEnum):
    KEYWORD = "keyword"
    SEMANTIC = "semantic"
    GRAPH = "graph"
    CANONICAL = "canonical"


class RetrievalPlanStep(BaseModel):
    signal: RetrievalSignal
    description: str
    result_count: int = 0


class Citation(BaseModel):
    citation_id: str
    chunk_id: UUID | None = None
    source_id: UUID | None = None
    source_object_version_id: UUID | None = None
    external_id: str | None = None
    excerpt: str
    score: float = 0.0
    signal: RetrievalSignal = RetrievalSignal.KEYWORD


class AnswerClaim(BaseModel):
    text: str
    confidence: float = Field(ge=0.0, le=1.0)
    citation_ids: list[str] = Field(default_factory=list)


class QuestionRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    mode: str = "hybrid"
    limit: int = Field(default=12, ge=1, le=30)


class QuestionAnswer(BaseModel):
    question: str
    answer: str
    confidence: float = Field(ge=0.0, le=1.0)
    insufficient_evidence: bool = False
    citations: list[Citation] = Field(default_factory=list)
    claims: list[AnswerClaim] = Field(default_factory=list)
    related_entity_ids: list[UUID] = Field(default_factory=list)
    retrieval_plan: list[RetrievalPlanStep] = Field(default_factory=list)
    model: str | None = None
    created_at: datetime
