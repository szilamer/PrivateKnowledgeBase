from typing import TypedDict
from uuid import UUID

from domain.entities import EntityMatch
from domain.extraction import ExtractedEntity


class EntityResolutionState(TypedDict, total=False):
    entity: ExtractedEntity
    owner_id: UUID
    candidates: list[EntityMatch]
    resolution_action: str
    resolution_matches: list[EntityMatch]
    proposal_type: str
    payload: dict[str, object]
    needs_review: bool
    risk_level: str
    pipeline_version: str
    error: str | None
