from domain.identity import OwnerContext
from domain.operations import (
    MaintenanceActionResult,
    OperationsStatus,
    PipelineHealthSnapshot,
)

from application.policy import LocalPolicyService
from application.ports.canonical import CanonicalRepository, OutboxRepository
from application.ports.maintenance import MaintenanceRecoveryDispatcher, PipelineHealthReader


def _build_summary_hu(pipeline: PipelineHealthSnapshot, status: OperationsStatus) -> str:
    parts = [
        f"Outbox várakozó: {status.pending_outbox_events}",
        f"Feldolgozás várakozó: {pipeline.extraction_pending}",
        f"Tudás várakozó: {pipeline.knowledge_pending}",
    ]
    if pipeline.extraction_failed > 0:
        parts.append(f"Feldolgozási hiba: {pipeline.extraction_failed}")
    if pipeline.embedding_model_mismatch_versions > 0:
        parts.append(f"Embedding eltérés: {pipeline.embedding_model_mismatch_versions}")
    return " · ".join(parts)


class MaintenanceService:
    """Phase I — proactive pipeline health checks and recovery actions."""

    def __init__(
        self,
        pipeline: PipelineHealthReader,
        canonical: CanonicalRepository,
        outbox: OutboxRepository,
        policy: LocalPolicyService,
        *,
        current_embedding_model: str,
        dispatcher: MaintenanceRecoveryDispatcher | None = None,
    ) -> None:
        self._pipeline = pipeline
        self._canonical = canonical
        self._outbox = outbox
        self._policy = policy
        self._embedding_model = current_embedding_model
        self._dispatcher = dispatcher

    async def get_extended_status(self, owner: OwnerContext) -> OperationsStatus:
        self._policy.authorize_owner(owner, owner.owner_id)
        owner_id = owner.owner_id
        pending = await self._outbox.pending_count()
        failed = await self._outbox.failed_count()
        raw = await self._pipeline.get_pipeline_snapshot(self._embedding_model)
        pipeline = PipelineHealthSnapshot(
            extraction_pending=raw.get("extraction_pending", 0),
            extraction_failed=raw.get("extraction_failed", 0),
            knowledge_pending=raw.get("knowledge_pending", 0),
            triage_pending=raw.get("triage_pending", 0),
            embedding_model_mismatch_versions=raw.get("embedding_model_mismatch_versions", 0),
        )
        status = OperationsStatus(
            pending_outbox_events=pending,
            failed_outbox_events=failed,
            processed_outbox_events=await self._outbox.processed_count(),
            canonical_entities=await self._canonical.count_entities(owner_id),
            canonical_claims=await self._canonical.count_claims(owner_id),
            projection_rebuild_recommended=failed > 0 or pending > 100,
            pipeline=pipeline,
            maintenance_recommended=(
                pipeline.extraction_pending > 0
                or pipeline.knowledge_pending > 0
                or pipeline.triage_pending > 0
                or pipeline.extraction_failed > 0
                or pipeline.embedding_model_mismatch_versions > 0
                or failed > 0
            ),
        )
        status.status_summary_hu = _build_summary_hu(pipeline, status)
        return status

    async def run_recovery(self, owner: OwnerContext) -> MaintenanceActionResult:
        self._policy.authorize_owner(owner, owner.owner_id)
        status = await self.get_extended_status(owner)
        result = MaintenanceActionResult()

        stalled = (
            status.pipeline.extraction_pending > 0
            or status.pipeline.knowledge_pending > 0
            or status.pipeline.triage_pending > 0
        )
        if stalled and self._dispatcher is not None:
            await self._dispatcher.enqueue_pipeline_recovery()
            result.pipeline_recovery_enqueued = True

        if status.pipeline.embedding_model_mismatch_versions > 0:
            flagged = await self._pipeline.flag_embedding_model_mismatch(self._embedding_model)
            result.embedding_mismatch_flagged = flagged

        return result
