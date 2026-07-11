from typing import Protocol
from uuid import UUID

from domain.ontology_proposals import (
    OntologyProposal,
    OntologyProposalStatus,
    UnmappedEntityCandidate,
    UnmappedRelationshipCandidate,
)


class OntologyProposalRepository(Protocol):
    async def create_proposals(
        self, proposals: list[OntologyProposal]
    ) -> list[OntologyProposal]: ...

    async def list_proposals(
        self,
        owner_id: UUID,
        *,
        status: OntologyProposalStatus | None = None,
        limit: int = 50,
    ) -> list[OntologyProposal]: ...

    async def get_by_id(self, proposal_id: UUID, owner_id: UUID) -> OntologyProposal | None: ...

    async def update_status(
        self,
        proposal_id: UUID,
        owner_id: UUID,
        *,
        status: OntologyProposalStatus,
        decision_rationale: str | None = None,
    ) -> OntologyProposal | None: ...

    async def find_pending_by_target_id(
        self,
        owner_id: UUID,
        *,
        kind: str,
        target_id: str,
    ) -> OntologyProposal | None: ...


class UnmappedConceptReader(Protocol):
    async def aggregate_unmapped_entities(
        self, owner_id: UUID, *, min_occurrences: int
    ) -> list[UnmappedEntityCandidate]: ...

    async def aggregate_unmapped_relationships(
        self, owner_id: UUID, *, min_occurrences: int
    ) -> list[UnmappedRelationshipCandidate]: ...
