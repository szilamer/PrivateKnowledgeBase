from uuid import UUID

from domain.canonical import CanonicalClaim, CanonicalEntity, ContradictionFinding
from domain.graph import GraphView
from domain.identity import OwnerContext

from application.policy import LocalPolicyService
from application.ports.canonical import CanonicalRepository
from application.ports.graph import GraphRepository


class CanonicalQueryService:
    """Read canonical entities, claims, and contradictions."""

    def __init__(
        self,
        canonical: CanonicalRepository,
        policy: LocalPolicyService,
    ) -> None:
        self._canonical = canonical
        self._policy = policy

    async def list_entities(
        self, owner: OwnerContext, *, limit: int = 50, cursor: UUID | None = None
    ) -> tuple[list[CanonicalEntity], UUID | None]:
        self._policy.authorize_owner(owner, owner.owner_id)
        return await self._canonical.list_entities(owner.owner_id, limit=limit, cursor=cursor)

    async def get_entity(self, owner: OwnerContext, entity_id: UUID) -> CanonicalEntity | None:
        self._policy.authorize_owner(owner, owner.owner_id)
        return await self._canonical.get_entity(entity_id, owner.owner_id)

    async def list_claims(
        self,
        owner: OwnerContext,
        *,
        limit: int = 50,
        cursor: UUID | None = None,
        status: str | None = "active",
    ) -> tuple[list[CanonicalClaim], UUID | None]:
        self._policy.authorize_owner(owner, owner.owner_id)
        return await self._canonical.list_claims(
            owner.owner_id, limit=limit, cursor=cursor, status=status
        )

    async def get_claim(self, owner: OwnerContext, claim_id: UUID) -> CanonicalClaim | None:
        self._policy.authorize_owner(owner, owner.owner_id)
        return await self._canonical.get_claim(claim_id, owner.owner_id)

    async def list_contradictions(
        self, owner: OwnerContext, *, status: str | None = "open", limit: int = 50
    ) -> list[ContradictionFinding]:
        self._policy.authorize_owner(owner, owner.owner_id)
        return await self._canonical.list_contradictions(owner.owner_id, status=status, limit=limit)


class GraphQueryService:
    """Bounded graph reads via GraphRepository (ADR-004)."""

    MAX_DEPTH = 3
    MAX_LIMIT = 200

    def __init__(self, graph: GraphRepository, policy: LocalPolicyService) -> None:
        self._graph = graph
        self._policy = policy

    async def neighborhood(
        self,
        owner: OwnerContext,
        entity_id: UUID,
        *,
        depth: int = 1,
        limit: int = 50,
    ) -> GraphView:
        self._policy.authorize_owner(owner, owner.owner_id)
        bounded_depth = min(max(depth, 1), self.MAX_DEPTH)
        bounded_limit = min(max(limit, 1), self.MAX_LIMIT)
        return await self._graph.get_entity_neighborhood(
            owner.owner_id,
            entity_id,
            depth=bounded_depth,
            limit=bounded_limit,
        )

    async def subgraph(
        self,
        owner: OwnerContext,
        *,
        root_entity_id: UUID | None = None,
        depth: int = 2,
        limit: int = 100,
    ) -> GraphView:
        self._policy.authorize_owner(owner, owner.owner_id)
        bounded_depth = min(max(depth, 1), self.MAX_DEPTH)
        bounded_limit = min(max(limit, 1), self.MAX_LIMIT)
        return await self._graph.get_bounded_subgraph(
            owner.owner_id,
            root_entity_id=root_entity_id,
            depth=bounded_depth,
            limit=bounded_limit,
        )
