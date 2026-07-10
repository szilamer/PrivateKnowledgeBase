from typing import Protocol
from uuid import UUID

from domain.canonical import (
    CanonicalClaim,
    CanonicalEntity,
    CanonicalRelationship,
    ClaimProvenance,
    ContradictionFinding,
    OutboxEvent,
)
from domain.proposals import KnowledgeProposal


class CanonicalRepository(Protocol):
    async def create_entity(self, entity: CanonicalEntity) -> CanonicalEntity: ...

    async def get_entity(self, entity_id: UUID, owner_id: UUID) -> CanonicalEntity | None: ...

    async def list_entities(
        self, owner_id: UUID, *, limit: int, cursor: UUID | None
    ) -> tuple[list[CanonicalEntity], UUID | None]: ...

    async def find_entity_by_name(
        self, owner_id: UUID, entity_type: str, canonical_name: str
    ) -> CanonicalEntity | None: ...

    async def create_claim(self, claim: CanonicalClaim) -> CanonicalClaim: ...

    async def get_claim(self, claim_id: UUID, owner_id: UUID) -> CanonicalClaim | None: ...

    async def list_claims(
        self, owner_id: UUID, *, limit: int, cursor: UUID | None, status: str | None = None
    ) -> tuple[list[CanonicalClaim], UUID | None]: ...

    async def find_active_claims(
        self,
        owner_id: UUID,
        *,
        subject_entity_id: UUID | None,
        predicate: str,
    ) -> list[CanonicalClaim]: ...

    async def add_provenance(self, provenance: ClaimProvenance) -> None: ...

    async def create_relationship(
        self, relationship: CanonicalRelationship
    ) -> CanonicalRelationship: ...

    async def create_contradiction(self, finding: ContradictionFinding) -> ContradictionFinding: ...

    async def list_contradictions(
        self, owner_id: UUID, *, status: str | None, limit: int
    ) -> list[ContradictionFinding]: ...

    async def link_entity_index(self, entity_index_id: UUID, canonical_entity_id: UUID) -> None: ...


class OutboxRepository(Protocol):
    async def append(self, event: OutboxEvent) -> None: ...

    async def fetch_pending(self, *, limit: int) -> list[OutboxEvent]: ...

    async def mark_processed(self, event_id: UUID) -> None: ...

    async def mark_failed(self, event_id: UUID, *, error: str) -> None: ...


class ProjectionDispatcher(Protocol):
    async def enqueue_projection(self) -> None: ...


class CanonicalMaterializer(Protocol):
    async def materialize_approved_proposal(
        self, owner_id: UUID, proposal: KnowledgeProposal
    ) -> None: ...
