import asyncio
from uuid import UUID

from adapters.extractors.heuristic import HeuristicExtractor
from adapters.llm.openai_compatible import OpenAICompatibleLLMProvider
from adapters.persistence.chunk_repository import PostgresChunkRepository
from adapters.persistence.knowledge_repository import (
    PostgresEntityIndexRepository,
    PostgresExtractionRunRepository,
    PostgresKnowledgeVersionRepository,
    PostgresProposalRepository,
)
from adapters.persistence.repositories import PostgresAuditRepository
from adapters.persistence.session import create_engine, create_session_factory, session_scope
from adapters.settings.runtime import load_resolved_llm_settings
from application.knowledge.extraction_service import KnowledgeExtractionService
from celery import Task
from observability.logging import get_logger

from worker.celery_app import celery_app
from worker.config import Settings

logger = get_logger("worker.tasks.knowledge_extraction")
settings = Settings()
_engine = create_engine(settings.database_url)
_session_factory = create_session_factory(_engine)


def _llm_provider() -> OpenAICompatibleLLMProvider | None:
    resolved = load_resolved_llm_settings(settings)
    if not resolved.llm_enabled:
        return None
    return OpenAICompatibleLLMProvider(resolved)


async def _extract_pending() -> int:
    async with session_scope(_session_factory) as session:
        service = KnowledgeExtractionService(
            versions=PostgresKnowledgeVersionRepository(session),
            chunks=PostgresChunkRepository(session),
            proposals=PostgresProposalRepository(session),
            runs=PostgresExtractionRunRepository(session),
            entities=PostgresEntityIndexRepository(session),
            llm=_llm_provider(),
            heuristic=HeuristicExtractor(),
            audit=PostgresAuditRepository(session),
        )
        return await service.process_pending()


async def _extract_version(version_id: UUID) -> int:
    async with session_scope(_session_factory) as session:
        service = KnowledgeExtractionService(
            versions=PostgresKnowledgeVersionRepository(session),
            chunks=PostgresChunkRepository(session),
            proposals=PostgresProposalRepository(session),
            runs=PostgresExtractionRunRepository(session),
            entities=PostgresEntityIndexRepository(session),
            llm=_llm_provider(),
            heuristic=HeuristicExtractor(),
            audit=PostgresAuditRepository(session),
        )
        return await service.extract_version(version_id)


@celery_app.task(name="worker.tasks.knowledge_extraction.extract_pending", bind=True)
def extract_pending(self: Task, **kwargs: object) -> dict[str, int]:
    logger.info("knowledge_extract_pending_started", task_id=self.request.id)
    count = asyncio.run(_extract_pending())
    return {"proposals": count}


@celery_app.task(name="worker.tasks.knowledge_extraction.extract_version", bind=True)
def extract_version(self: Task, version_id: str, **kwargs: object) -> dict[str, int]:
    logger.info(
        "knowledge_extract_version_started",
        version_id=version_id,
        task_id=self.request.id,
    )
    count = asyncio.run(_extract_version(UUID(version_id)))
    return {"proposals": count}
