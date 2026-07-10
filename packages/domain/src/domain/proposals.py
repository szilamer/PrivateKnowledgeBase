from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field


class ProposalType(StrEnum):
    ENTITY = "entity"
    CLAIM = "claim"
    RELATIONSHIP = "relationship"
    TASK = "task"
    DECISION = "decision"
    EVENT = "event"
    ENTITY_RESOLUTION = "entity_resolution"


class ProposalStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    DEFERRED = "deferred"
    MERGED = "merged"


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class EvidenceSpan(BaseModel):
    id: UUID
    proposal_id: UUID
    source_object_version_id: UUID
    content_chunk_id: UUID | None = None
    anchor_start: int | None = None
    anchor_end: int | None = None
    excerpt: str | None = None


class KnowledgeProposal(BaseModel):
    id: UUID
    owner_id: UUID
    extraction_run_id: UUID | None
    proposal_type: ProposalType
    status: ProposalStatus = ProposalStatus.PENDING
    risk_level: RiskLevel = RiskLevel.MEDIUM
    confidence: float = Field(ge=0.0, le=1.0)
    title: str
    payload: dict[str, object]
    project_id: UUID | None = None
    source_id: UUID | None = None
    requires_review: bool = True
    original_payload: dict[str, object] | None = None
    created_at: datetime
    updated_at: datetime
    evidence: list[EvidenceSpan] = Field(default_factory=list)


class ProposalFilter(BaseModel):
    proposal_type: ProposalType | None = None
    status: ProposalStatus | None = ProposalStatus.PENDING
    risk_level: RiskLevel | None = None
    source_id: UUID | None = None
    project_id: UUID | None = None
    min_confidence: float | None = None
    max_confidence: float | None = None
    limit: int = Field(default=50, ge=1, le=100)
    cursor: UUID | None = None
