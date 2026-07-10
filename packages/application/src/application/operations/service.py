from domain.identity import OwnerContext
from domain.operations import OperationsStatus, ProjectionRebuildResult

from application.operations.rebuild_service import GraphProjectionRebuildService
from application.operations.status_service import OperationsStatusService
from application.policy import LocalPolicyService
from application.ports.canonical import CanonicalRepository, OutboxRepository
from application.ports.graph import GraphProjector


class OperationsService:
    """Phase 6 — maintenance and operator endpoints."""

    def __init__(
        self,
        canonical: CanonicalRepository,
        outbox: OutboxRepository,
        policy: LocalPolicyService,
    ) -> None:
        self._canonical = canonical
        self._outbox = outbox
        self._policy = policy
        self._status = OperationsStatusService(canonical, outbox, policy)

    async def get_status(self, owner: OwnerContext) -> OperationsStatus:
        return await self._status.get_status(owner)

    async def rebuild_projection(
        self, owner: OwnerContext, projector: GraphProjector
    ) -> ProjectionRebuildResult:
        rebuild = GraphProjectionRebuildService(self._canonical, projector, self._policy)
        return await rebuild.rebuild(owner)
