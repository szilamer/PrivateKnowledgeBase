from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field


class AuditAction(StrEnum):
    SOURCE_REGISTERED = "source_registered"
    SOURCE_REMOVED = "source_removed"
    SYNC_STARTED = "sync_started"
    SYNC_COMPLETED = "sync_completed"
    SYNC_FAILED = "sync_failed"
    EXTRACTION_STARTED = "extraction_started"
    EXTRACTION_COMPLETED = "extraction_completed"
    EXTRACTION_FAILED = "extraction_failed"
    PROPOSAL_APPROVED = "proposal_approved"
    PROPOSAL_REJECTED = "proposal_rejected"
    PROPOSAL_DEFERRED = "proposal_deferred"
    PROPOSAL_EDITED = "proposal_edited"
    RETRIEVAL_PLANNED = "retrieval_planned"
    ONTOLOGY_PROPOSAL_CREATED = "ontology_proposal_created"
    ONTOLOGY_PROPOSAL_APPROVED = "ontology_proposal_approved"
    ONTOLOGY_PROPOSAL_REJECTED = "ontology_proposal_rejected"


class AuditEvent(BaseModel):
    id: UUID
    actor_id: UUID
    action: AuditAction
    object_type: str
    object_id: UUID
    correlation_id: str
    metadata: dict[str, object] = Field(default_factory=dict)
    created_at: datetime
