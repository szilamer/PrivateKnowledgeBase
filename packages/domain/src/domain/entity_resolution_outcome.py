from dataclasses import dataclass

from domain.entities import EntityMatch
from domain.extraction import ExtractedEntity
from domain.proposals import ProposalType

ENTITY_RESOLUTION_PIPELINE_VERSION = "v1"


@dataclass(frozen=True)
class EntityResolutionProposalSpec:
    """Deterministic output of the entity resolution agent before persistence."""

    entity: ExtractedEntity
    resolution_action: str
    proposal_type: ProposalType
    payload: dict[str, object]
    needs_review: bool
    risk_level: str
    candidates: list[EntityMatch]
