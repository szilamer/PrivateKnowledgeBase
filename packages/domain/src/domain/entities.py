from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field


class EntityType(StrEnum):
    PROJECT = "project"
    PERSON = "person"
    ORGANIZATION = "organization"
    DOCUMENT = "document"
    REPOSITORY = "repository"
    TECHNOLOGY = "technology"
    CONCEPT = "concept"
    SYSTEM_COMPONENT = "system_component"
    EXTERNAL_SYSTEM = "external_system"


class EntityIndexEntry(BaseModel):
    id: UUID
    owner_id: UUID
    entity_type: EntityType
    canonical_name: str
    aliases: list[str] = Field(default_factory=list)
    status: str = "proposed"
    source_proposal_id: UUID | None = None


class EntityMatch(BaseModel):
    entity_id: UUID
    canonical_name: str
    entity_type: EntityType
    score: float
    match_reason: str
