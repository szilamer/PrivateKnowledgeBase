from uuid import UUID

from adapters.connectors.google.factory import build_connector_factory, build_google_oauth
from adapters.persistence.repositories import (
    PostgresAuditRepository,
    PostgresSourceObjectRepository,
    PostgresSourceRepository,
    PostgresSyncRunRepository,
)
from application.sources.ingestion_runner import IngestionRunner
from celery import Task
from observability.logging import get_logger

from worker.celery_app import celery_app
from worker.config import Settings
from worker.db import run_task, task_session
from worker.pipeline import enqueue_extraction_process_pending

logger = get_logger("worker.tasks.ingestion")
settings = Settings()


async def _execute_sync(sync_run_id: UUID) -> None:
    async with task_session() as session:
        oauth = build_google_oauth(
            session=session,
            client_id=settings.google_client_id,
            client_secret=settings.google_client_secret,
            redirect_uri=settings.google_redirect_uri,
            session_secret=settings.session_secret,
            enabled=settings.pkb_google_connectors_enabled,
        )
        connector_factory = build_connector_factory(oauth)
        runner = IngestionRunner(
            sources=PostgresSourceRepository(session),
            sync_runs=PostgresSyncRunRepository(session),
            objects=PostgresSourceObjectRepository(session),
            audit=PostgresAuditRepository(session),
            connector=connector_factory,
        )
        result = await runner.run(sync_run_id)
        logger.info(
            "sync_completed",
            sync_run_id=str(result.id),
            status=result.status.value,
            processed=result.objects_processed,
            failed=result.objects_failed,
        )

    enqueue_extraction_process_pending()


@celery_app.task(
    name="worker.tasks.ingestion.run_sync",
    bind=True,
    autoretry_for=(ConnectionError, TimeoutError),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def run_sync(self: Task, sync_run_id: str, **kwargs: object) -> dict[str, str]:
    logger.info("sync_started", sync_run_id=sync_run_id, task_id=self.request.id)
    run_task(lambda: _execute_sync(UUID(sync_run_id)))
    return {"status": "done", "sync_run_id": sync_run_id}
