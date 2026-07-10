from domain.identity import OwnerContext
from domain.operations import OperationsStatus

from application.policy import LocalPolicyService
from application.ports.canonical import CanonicalRepository, OutboxRepository


class OperationsStatusService:
    """Phase 6 — operator visibility into projection pipeline health."""

    def __init__(
        self,
        canonical: CanonicalRepository,
        outbox: OutboxRepository,
        policy: LocalPolicyService,
    ) -> None:
        self._canonical = canonical
        self._outbox = outbox
        self._policy = policy

    async def get_status(self, owner: OwnerContext) -> OperationsStatus:
        self._policy.authorize_owner(owner, owner.owner_id)
        owner_id = owner.owner_id
        pending = await self._outbox.pending_count()
        failed = await self._outbox.failed_count()
        return OperationsStatus(
            pending_outbox_events=pending,
            failed_outbox_events=failed,
            processed_outbox_events=await self._outbox.processed_count(),
            canonical_entities=await self._canonical.count_entities(owner_id),
            canonical_claims=await self._canonical.count_claims(owner_id),
            projection_rebuild_recommended=failed > 0 or pending > 100,
        )
