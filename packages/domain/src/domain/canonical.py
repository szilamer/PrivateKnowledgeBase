from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field

from domain.entities import EntityType


class ClaimStatus(StrEnum):
    PROPOSED = "proposed"
    APPROVED = "approved"
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    REJECTED = "rejected"
    RETRACTED = "retracted"


class CanonicalEntity(BaseModel):
    id: UUID
    owner_id: UUID
    entity_type: EntityType
    canonical_name: str
    aliases: list[str] = Field(default_factory=list)
    description: str | None = None
    status: str = "active"
    source_proposal_id: UUID | None = None
    ontology_version: str = "0.1.0"
    created_at: datetime
    updated_at: datetime


class ClaimProvenance(BaseModel):
    id: UUID
    claim_id: UUID
    source_object_version_id: UUID | None = None
    content_chunk_id: UUID | None = None
    proposal_id: UUID | None = None
    extraction_run_id: UUID | None = None
    model: str | None = None
    confidence: float | None = None
    created_at: datetime


class CanonicalClaim(BaseModel):
    id: UUID
    owner_id: UUID
    subject_entity_id: UUID | None = None
    predicate: str
    object_value: str
    object_entity_id: UUID | None = None
    status: ClaimStatus = ClaimStatus.ACTIVE
    confidence: float = Field(ge=0.0, le=1.0)
    valid_from: datetime | None = None
    valid_to: datetime | None = None
    observed_at: datetime | None = None
    source_proposal_id: UUID | None = None
    superseded_by: UUID | None = None
    created_at: datetime
    updated_at: datetime
    provenance: list[ClaimProvenance] = Field(default_factory=list)


class CanonicalRelationship(BaseModel):
    id: UUID
    owner_id: UUID
    source_entity_id: UUID
    target_entity_id: UUID
    relationship_type: str
    status: str = "active"
    valid_from: datetime | None = None
    valid_to: datetime | None = None
    source_proposal_id: UUID | None = None
    created_at: datetime
    updated_at: datetime


class ContradictionStatus(StrEnum):
    OPEN = "open"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class ContradictionFinding(BaseModel):
    id: UUID
    owner_id: UUID
    existing_claim_id: UUID
    conflicting_claim_id: UUID | None = None
    conflicting_proposal_id: UUID | None = None
    status: ContradictionStatus = ContradictionStatus.OPEN
    summary: str
    evidence: dict[str, object] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class OutboxEventStatus(StrEnum):
    PENDING = "pending"
    PROCESSED = "processed"
    FAILED = "failed"


class OutboxEvent(BaseModel):
    id: UUID
    aggregate_type: str
    aggregate_id: str
    event_type: str
    payload: dict[str, object] = Field(default_factory=dict)
    created_at: datetime
    processed_at: datetime | None = None
    retry_count: int = 0
    status: OutboxEventStatus = OutboxEventStatus.PENDING
