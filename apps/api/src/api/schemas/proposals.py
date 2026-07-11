from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class EvidenceResponse(BaseModel):
    id: UUID
    source_object_version_id: UUID
    content_chunk_id: UUID | None
    anchor_start: int | None
    anchor_end: int | None
    excerpt: str | None


class ProposalResponse(BaseModel):
    id: UUID
    proposal_type: str
    status: str
    risk_level: str
    confidence: float
    title: str
    payload: dict[str, object]
    project_id: UUID | None
    source_id: UUID | None
    requires_review: bool
    created_at: datetime
    updated_at: datetime
    evidence: list[EvidenceResponse] = Field(default_factory=list)


class ProposalListResponse(BaseModel):
    items: list[ProposalResponse]
    next_cursor: UUID | None


class ApproveRequest(BaseModel):
    rationale: str | None = None


class RejectRequest(BaseModel):
    rationale: str | None = None


class DeferRequest(BaseModel):
    rationale: str | None = None


class EditApproveRequest(BaseModel):
    edited_payload: dict[str, object]
    rationale: str | None = None


class MergeEntitiesRequest(BaseModel):
    source_entity_id: UUID
    target_entity_id: UUID
    rationale: str | None = None


class BatchApproveRequest(BaseModel):
    proposal_ids: list[UUID] = Field(min_length=1, max_length=50)


class AutoApproveResponse(BaseModel):
    approved_count: int
    message: str
