from domain.identity import OwnerContext
from domain.operations import MaintenanceActionResult, OperationsStatus, ProjectionRebuildResult

from application.operations.maintenance_service import MaintenanceService
from application.operations.rebuild_service import GraphProjectionRebuildService
from application.policy import LocalPolicyService
from application.ports.canonical import CanonicalRepository, OutboxRepository
from application.ports.graph import GraphProjector
from application.ports.maintenance import MaintenanceRecoveryDispatcher, PipelineHealthReader


class OperationsService:
    """Phase 6 / I — maintenance and operator endpoints."""

    def __init__(
        self,
        canonical: CanonicalRepository,
        outbox: OutboxRepository,
        policy: LocalPolicyService,
        pipeline: PipelineHealthReader,
        *,
        current_embedding_model: str,
        dispatcher: MaintenanceRecoveryDispatcher | None = None,
    ) -> None:
        self._canonical = canonical
        self._outbox = outbox
        self._policy = policy
        self._maintenance = MaintenanceService(
            pipeline,
            canonical,
            outbox,
            policy,
            current_embedding_model=current_embedding_model,
            dispatcher=dispatcher,
        )

    async def get_status(self, owner: OwnerContext) -> OperationsStatus:
        return await self._maintenance.get_extended_status(owner)

    async def run_recovery(self, owner: OwnerContext) -> MaintenanceActionResult:
        return await self._maintenance.run_recovery(owner)

    async def rebuild_projection(
        self, owner: OwnerContext, projector: GraphProjector
    ) -> ProjectionRebuildResult:
        rebuild = GraphProjectionRebuildService(self._canonical, projector, self._policy)
        return await rebuild.rebuild(owner)
