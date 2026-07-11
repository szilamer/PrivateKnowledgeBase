from pathlib import Path
from uuid import UUID

from adapters.embeddings.factory import build_embedding_provider
from adapters.graph.projector import Neo4jGraphProjector
from adapters.persistence.canonical_repository import (
    PostgresCanonicalRepository,
    PostgresOutboxRepository,
)
from adapters.persistence.pipeline_health_repository import PostgresPipelineHealthRepository
from adapters.settings.config_loader import load_app_settings
from adapters.settings.runtime import load_resolved_llm_settings
from application.operations.service import OperationsService
from application.policy import LocalPolicyService
from celery import Task
from domain.identity import DEFAULT_OWNER_ID, OwnerContext
from observability.logging import get_logger

from worker.celery_app import celery_app
from worker.config import Settings
from worker.db import run_task, task_session
from worker.pipeline import enqueue_pipeline_recovery

logger = get_logger("worker.tasks.maintenance")
settings = Settings()


class WorkerMaintenanceDispatcher:
    async def enqueue_pipeline_recovery(self) -> None:
        enqueue_pipeline_recovery()

    async def schedule_maintenance_check(self, *, delay_seconds: int) -> None:
        celery_app.send_task(
            "worker.tasks.maintenance.run_health_check",
            countdown=delay_seconds,
            queue="maintenance",
        )


def _embedding_model() -> str:
    return build_embedding_provider(load_resolved_llm_settings(settings)).model


def _maintenance_interval_seconds() -> int:
    app_settings = load_app_settings(Path(settings.settings_config_path))
    if app_settings is None or not app_settings.maintenance.enabled:
        return 0
    return max(5, app_settings.maintenance.interval_minutes) * 60


def _build_operations(session: object) -> OperationsService:
    from sqlalchemy.ext.asyncio import AsyncSession

    assert isinstance(session, AsyncSession)
    return OperationsService(
        PostgresCanonicalRepository(session),
        PostgresOutboxRepository(session),
        LocalPolicyService(),
        PostgresPipelineHealthRepository(session),
        current_embedding_model=_embedding_model(),
        dispatcher=WorkerMaintenanceDispatcher(),
    )


async def _rebuild_projection(owner_id: UUID) -> dict[str, int | bool]:
    projector = Neo4jGraphProjector(settings)
    try:
        async with task_session() as session:
            result = await _build_operations(session).rebuild_projection(
                OwnerContext(owner_id=owner_id),
                projector,
            )
            return {
                "entities_projected": result.entities_projected,
                "relationships_projected": result.relationships_projected,
                "claims_projected": result.claims_projected,
                "contradictions_projected": result.contradictions_projected,
                "cleared_nodes": result.cleared_nodes,
            }
    finally:
        await projector.close()


async def _run_health_check(owner_id: UUID) -> dict[str, object]:
    async with task_session() as session:
        operations = _build_operations(session)
        owner = OwnerContext(owner_id=owner_id)
        result = await operations.run_recovery(owner)
        status = await operations.get_status(owner)
    interval = _maintenance_interval_seconds()
    if interval > 0:
        dispatcher = WorkerMaintenanceDispatcher()
        await dispatcher.schedule_maintenance_check(delay_seconds=interval)
    logger.info(
        "maintenance_health_check_complete",
        owner_id=str(owner_id),
        pipeline_recovery=result.pipeline_recovery_enqueued,
        embedding_flagged=result.embedding_mismatch_flagged,
        next_check_seconds=interval,
    )
    return {
        "pipeline_recovery_enqueued": result.pipeline_recovery_enqueued,
        "embedding_mismatch_flagged": result.embedding_mismatch_flagged,
        "status_summary_hu": status.status_summary_hu,
        "maintenance_recommended": status.maintenance_recommended,
    }


async def _recover_pipeline() -> dict[str, str]:
    enqueue_pipeline_recovery()
    return {"status": "enqueued"}


@celery_app.task(name="worker.tasks.maintenance.rebuild_projection", bind=True)
def rebuild_projection(
    self: Task, owner_id: str | None = None, **kwargs: object
) -> dict[str, int | bool]:
    resolved_owner = UUID(owner_id) if owner_id else DEFAULT_OWNER_ID
    logger.info(
        "projection_rebuild_started",
        task_id=self.request.id,
        owner_id=str(resolved_owner),
    )
    return run_task(lambda: _rebuild_projection(resolved_owner))


@celery_app.task(name="worker.tasks.maintenance.run_health_check", bind=True)
def run_health_check(
    self: Task,
    owner_id: str | None = None,
    **kwargs: object,
) -> dict[str, object]:
    resolved_owner = UUID(owner_id) if owner_id else DEFAULT_OWNER_ID
    logger.info("maintenance_health_check_started", task_id=self.request.id)
    return run_task(lambda: _run_health_check(resolved_owner))


@celery_app.task(name="worker.tasks.maintenance.recover_pipeline", bind=True)
def recover_pipeline(self: Task, **kwargs: object) -> dict[str, str]:
    logger.info("maintenance_recover_pipeline_started", task_id=self.request.id)
    return run_task(_recover_pipeline)


@celery_app.task(name="worker.tasks.maintenance.ping", bind=True)
def ping(self: Task, **kwargs: object) -> dict[str, str]:
    logger.info("worker_ping", task_id=self.request.id)
    return {"status": "ok", "queue": "maintenance"}
