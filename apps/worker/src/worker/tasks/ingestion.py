import asyncio
from uuid import UUID

from adapters.connectors.factory import ConnectorFactory
from adapters.persistence.repositories import (
    PostgresAuditRepository,
    PostgresSourceObjectRepository,
    PostgresSourceRepository,
    PostgresSyncRunRepository,
)
from adapters.persistence.session import create_engine, create_session_factory, session_scope
from application.sources.ingestion_runner import IngestionRunner
from celery import Task
from observability.logging import get_logger

from worker.celery_app import celery_app
from worker.config import Settings

logger = get_logger("worker.tasks.ingestion")
settings = Settings()
_engine = create_engine(settings.database_url)
_session_factory = create_session_factory(_engine)
_connector_factory = ConnectorFactory()


async def _execute_sync(sync_run_id: UUID) -> None:
    async with session_scope(_session_factory) as session:
        runner = IngestionRunner(
            sources=PostgresSourceRepository(session),
            sync_runs=PostgresSyncRunRepository(session),
            objects=PostgresSourceObjectRepository(session),
            audit=PostgresAuditRepository(session),
            connector=_connector_factory,
        )
        result = await runner.run(sync_run_id)
        logger.info(
            "sync_completed",
            sync_run_id=str(result.id),
            status=result.status.value,
            processed=result.objects_processed,
            failed=result.objects_failed,
        )

    from celery import Celery

    client = Celery(broker=settings.celery_broker_url)
    client.send_task(
        "worker.tasks.extraction.process_pending",
        queue="extraction",
    )


@celery_app.task(
    name="worker.tasks.ingestion.run_sync",
    bind=True,
    autoretry_for=(ConnectionError, TimeoutError),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def run_sync(self: Task, sync_run_id: str, **kwargs: object) -> dict[str, str]:
    logger.info("sync_started", sync_run_id=sync_run_id, task_id=self.request.id)
    asyncio.run(_execute_sync(UUID(sync_run_id)))
    return {"status": "done", "sync_run_id": sync_run_id}
