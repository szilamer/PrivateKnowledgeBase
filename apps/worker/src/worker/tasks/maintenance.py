from observability.logging import get_logger

from worker.celery_app import celery_app

logger = get_logger("worker.tasks.maintenance")


@celery_app.task(name="worker.tasks.maintenance.ping", bind=True)
def ping(self) -> dict[str, str]:
    logger.info("worker_ping", task_id=self.request.id)
    return {"status": "ok", "queue": "maintenance"}
