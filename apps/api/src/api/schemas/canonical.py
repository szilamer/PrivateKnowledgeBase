from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class EntityResponse(BaseModel):
    id: UUID
    entity_type: str
    canonical_name: str
    aliases: list[str] = Field(default_factory=list)
    description: str | None = None
    status: str
    source_proposal_id: UUID | None = None
    created_at: datetime
    updated_at: datetime


class EntityListResponse(BaseModel):
    items: list[EntityResponse]
    next_cursor: UUID | None


class ProvenanceResponse(BaseModel):
    id: UUID
    source_object_version_id: UUID | None
    content_chunk_id: UUID | None
    proposal_id: UUID | None
    confidence: float | None = None


class ClaimResponse(BaseModel):
    id: UUID
    subject_entity_id: UUID | None
    predicate: str
    object_value: str
    status: str
    confidence: float
    valid_from: datetime | None = None
    valid_to: datetime | None = None
    source_proposal_id: UUID | None = None
    provenance: list[ProvenanceResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class ClaimListResponse(BaseModel):
    items: list[ClaimResponse]
    next_cursor: UUID | None


class ContradictionResponse(BaseModel):
    id: UUID
    existing_claim_id: UUID
    conflicting_claim_id: UUID | None
    conflicting_proposal_id: UUID | None
    status: str
    summary: str
    predicate: str | None = None
    existing_value: str | None = None
    conflicting_value: str | None = None
    subject_entity_id: UUID | None = None
    created_at: datetime


class ContradictionListResponse(BaseModel):
    items: list[ContradictionResponse]


class GraphNodeResponse(BaseModel):
    id: str
    label: str
    node_type: str
    properties: dict[str, object] = Field(default_factory=dict)


class GraphEdgeResponse(BaseModel):
    id: str
    source_id: str
    target_id: str
    edge_type: str
    properties: dict[str, object] = Field(default_factory=dict)


class GraphViewResponse(BaseModel):
    root_id: UUID | None
    depth: int
    nodes: list[GraphNodeResponse]
    edges: list[GraphEdgeResponse]
    truncated: bool
