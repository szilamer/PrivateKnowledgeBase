import asyncio

from adapters.graph.projector import Neo4jGraphProjector
from adapters.persistence.canonical_repository import PostgresOutboxRepository
from adapters.persistence.session import create_engine, create_session_factory, session_scope
from application.canonical.projection_service import GraphProjectionService
from celery import Task
from observability.logging import get_logger

from worker.celery_app import celery_app
from worker.config import Settings

logger = get_logger("worker.tasks.graph_projection")
settings = Settings()
_engine = create_engine(settings.database_url)
_session_factory = create_session_factory(_engine)


async def _process_pending() -> int:
    projector = Neo4jGraphProjector(settings)
    try:
        async with session_scope(_session_factory) as session:
            service = GraphProjectionService(
                outbox=PostgresOutboxRepository(session),
                projector=projector,
            )
            return await service.process_pending()
    finally:
        await projector.close()


@celery_app.task(name="worker.tasks.graph_projection.process_pending", bind=True)
def process_pending(self: Task, **kwargs: object) -> dict[str, int]:
    logger.info("graph_projection_started", task_id=self.request.id)
    count = asyncio.run(_process_pending())
    return {"projected": count}
