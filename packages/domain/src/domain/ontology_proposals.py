from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field

ONTOLOGY_CURATOR_PIPELINE_VERSION = "v1"
MIN_UNMAPPED_OCCURRENCES = 3


class OntologyProposalKind(StrEnum):
    ENTITY_TYPE = "entity_type"
    RELATIONSHIP_TYPE = "relationship_type"
    ALIAS = "alias"


class OntologyProposalStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class UnmappedEntityCandidate(BaseModel):
    name: str
    entity_type: str
    occurrence_count: int
    sample_proposal_ids: list[str] = Field(default_factory=list)


class UnmappedRelationshipCandidate(BaseModel):
    relationship_type: str
    occurrence_count: int
    sample_proposal_ids: list[str] = Field(default_factory=list)


class OntologyProposal(BaseModel):
    id: UUID
    owner_id: UUID
    kind: OntologyProposalKind
    status: OntologyProposalStatus
    title: str
    rationale: str
    proposed_definition: dict[str, object]
    evidence: dict[str, object] = Field(default_factory=dict)
    ontology_version: str
    created_at: datetime
    updated_at: datetime
    decided_at: datetime | None = None
    decision_rationale: str | None = None
