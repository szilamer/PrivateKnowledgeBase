import asyncio
from uuid import UUID

from adapters.content.loader import LocalAndGitHubContentLoader
from adapters.embeddings.factory import build_embedding_provider
from adapters.parsers.factory import ParserFactory
from adapters.persistence.chunk_repository import (
    PostgresChunkRepository,
    PostgresVersionContentRepository,
)
from adapters.persistence.session import create_engine, create_session_factory, session_scope
from application.content.processing import DocumentProcessingService
from application.ports.content import EmbeddingProvider
from celery import Task
from observability.logging import get_logger

from worker.celery_app import celery_app
from worker.config import Settings

logger = get_logger("worker.tasks.extraction")
settings = Settings()
_engine = create_engine(settings.database_url)
_session_factory = create_session_factory(_engine)


def _embedding_provider() -> EmbeddingProvider:
    return build_embedding_provider(settings)


async def _process_pending() -> int:
    async with session_scope(_session_factory) as session:
        processor = DocumentProcessingService(
            versions=PostgresVersionContentRepository(session),
            chunks=PostgresChunkRepository(session),
            embeddings=_embedding_provider(),
            parser=ParserFactory(),
            loader=LocalAndGitHubContentLoader(),
        )
        count = await processor.process_pending()
    if count > 0:
        from celery import Celery

        client = Celery(broker=settings.celery_broker_url)
        client.send_task(
            "worker.tasks.knowledge_extraction.extract_pending",
            queue="extraction",
        )
    return count


async def _process_version(version_id: UUID) -> int:
    async with session_scope(_session_factory) as session:
        processor = DocumentProcessingService(
            versions=PostgresVersionContentRepository(session),
            chunks=PostgresChunkRepository(session),
            embeddings=_embedding_provider(),
            parser=ParserFactory(),
            loader=LocalAndGitHubContentLoader(),
        )
        chunk_count = await processor.process_version(version_id)
    if chunk_count > 0:
        from celery import Celery

        client = Celery(broker=settings.celery_broker_url)
        client.send_task(
            "worker.tasks.knowledge_extraction.extract_version",
            args=[str(version_id)],
            queue="extraction",
        )
    return chunk_count


@celery_app.task(name="worker.tasks.extraction.process_pending", bind=True)
def process_pending(self: Task, **kwargs: object) -> dict[str, int]:
    logger.info("process_pending_started", task_id=self.request.id)
    count = asyncio.run(_process_pending())
    return {"processed": count}


@celery_app.task(name="worker.tasks.extraction.process_version", bind=True)
def process_version(self: Task, version_id: str, **kwargs: object) -> dict[str, int]:
    logger.info("process_version_started", version_id=version_id, task_id=self.request.id)
    count = asyncio.run(_process_version(UUID(version_id)))
    return {"chunks": count}
