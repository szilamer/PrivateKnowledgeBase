from celery import Celery
from observability.logging import configure_logging, get_logger

from worker.config import Settings

settings = Settings()
configure_logging(settings.log_level)
logger = get_logger("worker")

celery_app = Celery(
    "pkb-worker",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_default_queue="maintenance",
    task_routes={
        "worker.tasks.ingestion.*": {"queue": "ingestion"},
        "worker.tasks.extraction.*": {"queue": "extraction"},
        "worker.tasks.knowledge_extraction.*": {"queue": "extraction"},
        "worker.tasks.embedding.*": {"queue": "embedding"},
        "worker.tasks.graph_projection.*": {"queue": "graph_projection"},
        "worker.tasks.maintenance.*": {"queue": "maintenance"},
    },
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

celery_app.autodiscover_tasks(["worker"])

# Ensure task modules are registered (autodiscover alone misses src-layout submodules).
import worker.recovery  # noqa: F401, E402 — re-queue pending sync runs on startup
import worker.tasks.extraction  # noqa: F401, E402
import worker.tasks.graph_projection  # noqa: F401, E402
import worker.tasks.ingestion  # noqa: F401, E402
import worker.tasks.knowledge_extraction  # noqa: F401, E402
import worker.tasks.maintenance  # noqa: F401, E402
import worker.tasks.reports  # noqa: F401, E402
