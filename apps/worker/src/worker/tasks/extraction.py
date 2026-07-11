from pathlib import Path
from uuid import UUID

from adapters.embeddings.factory import build_embedding_provider
from adapters.parsers.factory import ParserFactory
from adapters.persistence.chunk_repository import (
    PostgresChunkRepository,
    PostgresVersionContentRepository,
)
from adapters.settings.config_loader import load_app_settings
from adapters.settings.runtime import load_resolved_llm_settings
from application.content.processing import DocumentProcessingService
from application.ports.content import EmbeddingProvider
from application.sources.triage_service import VersionTriageService
from celery import Task
from observability.logging import get_logger

from worker.celery_app import celery_app
from worker.config import Settings
from worker.db import run_task, task_session
from worker.deps import build_content_loader
from worker.pipeline import enqueue_extraction_process_pending, enqueue_knowledge_extract_pending

logger = get_logger("worker.tasks.extraction")
settings = Settings()

BATCH_SIZE = 20


def _embedding_provider() -> EmbeddingProvider:
    return build_embedding_provider(load_resolved_llm_settings(settings))


def _build_processor(session: object) -> DocumentProcessingService:
    from sqlalchemy.ext.asyncio import AsyncSession

    assert isinstance(session, AsyncSession)
    return DocumentProcessingService(
        versions=PostgresVersionContentRepository(session),
        chunks=PostgresChunkRepository(session),
        embeddings=_embedding_provider(),
        parser=ParserFactory(),
        loader=build_content_loader(session, settings),
    )


async def _run_triage_if_enabled(session: object) -> int:
    app_settings = load_app_settings(Path(settings.settings_config_path))
    if app_settings is None or not app_settings.agents.triage.enabled:
        return 0
    triage = VersionTriageService(PostgresVersionContentRepository(session))  # type: ignore[arg-type]
    return await triage.process_pending(batch_size=BATCH_SIZE)


async def _process_pending() -> dict[str, int]:
    async with task_session() as session:
        triaged = await _run_triage_if_enabled(session)
        processor = _build_processor(session)
        processed = await processor.process_pending(batch_size=BATCH_SIZE)
        remaining = await PostgresVersionContentRepository(session).count_pending_extractions()
        triage_remaining = 0
        if triaged > 0:
            triage_remaining = len(
                await PostgresVersionContentRepository(session).get_versions_needing_triage(limit=1)
            )

    if remaining > 0 or triage_remaining > 0:
        enqueue_extraction_process_pending()
    if processed > 0 or remaining == 0:
        enqueue_knowledge_extract_pending()

    logger.info(
        "process_pending_complete",
        processed=processed,
        remaining_extractions=remaining,
    )
    return {"processed": processed, "remaining": remaining}


async def _process_version(version_id: UUID) -> int:
    async with task_session() as session:
        processor = _build_processor(session)
        chunk_count = await processor.process_version(version_id)

    if chunk_count > 0:
        from celery import Celery

        Celery(broker=settings.celery_broker_url).send_task(
            "worker.tasks.knowledge_extraction.extract_version",
            args=[str(version_id)],
            queue="extraction",
        )
    return chunk_count


@celery_app.task(name="worker.tasks.extraction.process_pending", bind=True)
def process_pending(self: Task, **kwargs: object) -> dict[str, int]:
    logger.info("process_pending_started", task_id=self.request.id)
    return run_task(_process_pending)


@celery_app.task(name="worker.tasks.extraction.process_version", bind=True)
def process_version(self: Task, version_id: str, **kwargs: object) -> dict[str, int]:
    logger.info("process_version_started", version_id=version_id, task_id=self.request.id)
    count = run_task(lambda: _process_version(UUID(version_id)))
    return {"chunks": count}
