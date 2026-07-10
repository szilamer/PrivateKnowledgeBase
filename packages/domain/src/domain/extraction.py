"""Versioned extraction output schemas (FR-KNW-001, FR-KNW-002)."""

from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field

from domain.entities import EntityType

EXTRACTION_SCHEMA_VERSION = "1.0.0"
EXTRACTION_PROMPT_VERSION = "extraction_v1"
EXTRACTION_PIPELINE_VERSION = "0.1.0"


class ExtractedEntity(BaseModel):
    local_id: str
    name: str
    entity_type: EntityType
    aliases: list[str] = Field(default_factory=list)
    description: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    chunk_id: UUID | None = None
    anchor_start: int | None = None
    anchor_end: int | None = None


class ExtractedClaim(BaseModel):
    local_id: str
    subject_local_id: str
    predicate: str
    value: str
    confidence: float = Field(ge=0.0, le=1.0)
    valid_from: str | None = None
    valid_to: str | None = None
    chunk_id: UUID | None = None
    anchor_start: int | None = None
    anchor_end: int | None = None


class ExtractedRelationship(BaseModel):
    local_id: str
    source_local_id: str
    target_local_id: str
    relationship_type: str
    confidence: float = Field(ge=0.0, le=1.0)
    chunk_id: UUID | None = None


class ExtractedTask(BaseModel):
    local_id: str
    title: str
    description: str | None = None
    status: str | None = None
    assignee_local_id: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    chunk_id: UUID | None = None


class ExtractedDecision(BaseModel):
    local_id: str
    title: str
    rationale: str | None = None
    status: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    chunk_id: UUID | None = None


class ExtractedEvent(BaseModel):
    local_id: str
    title: str
    event_type: str | None = None
    occurred_at: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    chunk_id: UUID | None = None


class ExtractionResult(BaseModel):
    schema_version: str = EXTRACTION_SCHEMA_VERSION
    entities: list[ExtractedEntity] = Field(default_factory=list)
    claims: list[ExtractedClaim] = Field(default_factory=list)
    relationships: list[ExtractedRelationship] = Field(default_factory=list)
    tasks: list[ExtractedTask] = Field(default_factory=list)
    decisions: list[ExtractedDecision] = Field(default_factory=list)
    events: list[ExtractedEvent] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class KnowledgeStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ExtractionRunStatus(StrEnum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
