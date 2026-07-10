import asyncio
from uuid import UUID

from adapters.graph.projector import Neo4jGraphProjector
from adapters.persistence.canonical_repository import (
    PostgresCanonicalRepository,
    PostgresOutboxRepository,
)
from adapters.persistence.session import create_engine, create_session_factory, session_scope
from application.operations.service import OperationsService
from application.policy import LocalPolicyService
from celery import Task
from domain.identity import DEFAULT_OWNER_ID, OwnerContext
from observability.logging import get_logger

from worker.celery_app import celery_app
from worker.config import Settings

logger = get_logger("worker.tasks.maintenance")
settings = Settings()
_engine = create_engine(settings.database_url)
_session_factory = create_session_factory(_engine)


async def _rebuild_projection(owner_id: UUID) -> dict[str, int | bool]:
    projector = Neo4jGraphProjector(settings)
    try:
        async with session_scope(_session_factory) as session:
            operations = OperationsService(
                PostgresCanonicalRepository(session),
                PostgresOutboxRepository(session),
                LocalPolicyService(),
            )
            result = await operations.rebuild_projection(
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
    return asyncio.run(_rebuild_projection(resolved_owner))


@celery_app.task(name="worker.tasks.maintenance.ping", bind=True)
def ping(self: Task, **kwargs: object) -> dict[str, str]:
    logger.info("worker_ping", task_id=self.request.id)
    return {"status": "ok", "queue": "maintenance"}
