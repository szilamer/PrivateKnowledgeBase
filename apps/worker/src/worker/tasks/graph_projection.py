from adapters.graph.projector import Neo4jGraphProjector
from adapters.persistence.canonical_repository import PostgresOutboxRepository
from application.canonical.projection_service import GraphProjectionService
from celery import Task
from observability.logging import get_logger

from worker.celery_app import celery_app
from worker.config import Settings
from worker.db import run_task, task_session
from worker.pipeline import enqueue_graph_projection_pending

logger = get_logger("worker.tasks.graph_projection")
settings = Settings()

BATCH_SIZE = 50


async def _process_pending() -> dict[str, int]:
    projector = Neo4jGraphProjector(settings)
    try:
        async with task_session() as session:
            outbox = PostgresOutboxRepository(session)
            service = GraphProjectionService(outbox=outbox, projector=projector)
            projected = await service.process_pending(batch_size=BATCH_SIZE)
            remaining = await outbox.pending_count()
    finally:
        await projector.close()

    if remaining > 0:
        enqueue_graph_projection_pending()

    logger.info(
        "graph_projection_complete",
        projected=projected,
        remaining_outbox=remaining,
    )
    return {"projected": projected, "remaining": remaining}


@celery_app.task(name="worker.tasks.graph_projection.process_pending", bind=True)
def process_pending(self: Task, **kwargs: object) -> dict[str, int]:
    logger.info("graph_projection_started", task_id=self.request.id)
    return run_task(_process_pending)
