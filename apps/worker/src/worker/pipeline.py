"""Centralized Celery enqueue helpers for the processing pipeline."""

from celery import Celery

from worker.config import Settings

settings = Settings()


def _client() -> Celery:
    return Celery(broker=settings.celery_broker_url)


def enqueue_extraction_process_pending() -> None:
    _client().send_task(
        "worker.tasks.extraction.process_pending",
        queue="extraction",
    )


def enqueue_knowledge_extract_pending() -> None:
    _client().send_task(
        "worker.tasks.knowledge_extraction.extract_pending",
        queue="extraction",
    )


def enqueue_graph_projection_pending() -> None:
    _client().send_task(
        "worker.tasks.graph_projection.process_pending",
        queue="graph_projection",
    )


def enqueue_pipeline_recovery() -> None:
    """Kick off all pipeline stages; each stage re-chains until its queue is empty."""
    enqueue_extraction_process_pending()
    enqueue_knowledge_extract_pending()
    enqueue_graph_projection_pending()
