from typing import TypedDict
from uuid import UUID

from domain.ontology_proposals import (
    OntologyProposal,
    UnmappedEntityCandidate,
    UnmappedRelationshipCandidate,
)
from ontology.loader import OntologySnapshot


class OntologyCuratorState(TypedDict, total=False):
    owner_id: UUID
    ontology: OntologySnapshot
    unmapped_entities: list[UnmappedEntityCandidate]
    unmapped_relationships: list[UnmappedRelationshipCandidate]
    proposals: list[OntologyProposal]
    pipeline_version: str
    error: str | None
