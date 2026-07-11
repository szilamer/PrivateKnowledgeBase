from adapters.persistence.repositories import PostgresSyncRunRepository
from adapters.tasks.celery_dispatcher import CeleryTaskDispatcher
from celery.signals import worker_ready
from domain.sync import SyncRunStatus
from observability.logging import get_logger

from worker.config import Settings
from worker.db import run_task, task_session
from worker.pipeline import enqueue_pipeline_recovery

logger = get_logger("worker.recovery")
settings = Settings()


async def recover_pending_sync_runs() -> int:
    dispatcher = CeleryTaskDispatcher(settings.celery_broker_url)
    async with task_session() as session:
        repo = PostgresSyncRunRepository(session)
        pending = await repo.list_by_status(SyncRunStatus.PENDING, limit=100)
        for run in pending:
            await dispatcher.enqueue_sync_run(run.id)
            logger.info("requeued_pending_sync", sync_run_id=str(run.id))
    return len(pending)


@worker_ready.connect  # type: ignore[untyped-decorator]
def on_worker_ready(sender: object | None = None, **kwargs: object) -> None:
    del sender, kwargs
    try:
        sync_count = run_task(recover_pending_sync_runs)
        if sync_count:
            logger.info("pending_sync_recovery_complete", requeued=sync_count)
    except Exception as exc:  # noqa: BLE001 — worker must start even if recovery fails
        logger.error("pending_sync_recovery_failed", error=str(exc))

    try:
        enqueue_pipeline_recovery()
        logger.info("pipeline_recovery_enqueued")
    except Exception as exc:  # noqa: BLE001
        logger.error("pipeline_recovery_failed", error=str(exc))
