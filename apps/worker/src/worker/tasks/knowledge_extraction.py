from uuid import UUID, uuid4

from adapters.extractors.heuristic import HeuristicExtractor
from adapters.llm.openai_compatible import OpenAICompatibleLLMProvider
from adapters.persistence.canonical_repository import (
    PostgresCanonicalRepository,
    PostgresOutboxRepository,
)
from adapters.persistence.chunk_repository import PostgresChunkRepository
from adapters.persistence.knowledge_repository import (
    PostgresApprovalRepository,
    PostgresEntityIndexRepository,
    PostgresExtractionRunRepository,
    PostgresKnowledgeVersionRepository,
    PostgresProposalRepository,
)
from adapters.persistence.repositories import PostgresAuditRepository
from adapters.settings.runtime import load_resolved_llm_settings
from adapters.tasks.celery_dispatcher import CeleryTaskDispatcher
from application.canonical.materialization_service import CanonicalMaterializationService
from application.knowledge.extraction_service import KnowledgeExtractionService
from application.knowledge.proposal_service import ProposalService
from application.policy import LocalPolicyService
from celery import Task
from domain.identity import DEFAULT_OWNER_ID, OwnerContext
from observability.logging import get_logger

from worker.celery_app import celery_app
from worker.config import Settings
from worker.db import run_task, task_session
from worker.pipeline import enqueue_graph_projection_pending, enqueue_knowledge_extract_pending

logger = get_logger("worker.tasks.knowledge_extraction")
settings = Settings()

BATCH_SIZE = 10


def _llm_provider() -> OpenAICompatibleLLMProvider | None:
    resolved = load_resolved_llm_settings(settings)
    if not resolved.llm_enabled:
        return None
    return OpenAICompatibleLLMProvider(resolved)


def _build_proposal_service(session: object) -> ProposalService:
    from sqlalchemy.ext.asyncio import AsyncSession

    assert isinstance(session, AsyncSession)
    proposal_repo = PostgresProposalRepository(session)
    approval_repo = PostgresApprovalRepository(session)
    entity_repo = PostgresEntityIndexRepository(session)
    canonical_repo = PostgresCanonicalRepository(session)
    outbox_repo = PostgresOutboxRepository(session)
    materializer = CanonicalMaterializationService(canonical_repo, outbox_repo, entity_repo)
    dispatcher = CeleryTaskDispatcher(settings.celery_broker_url)
    return ProposalService(
        proposal_repo,
        approval_repo,
        materializer,
        PostgresAuditRepository(session),
        LocalPolicyService(),
        on_materialized=dispatcher,
    )


def _build_extraction_service(session: object) -> KnowledgeExtractionService:
    from sqlalchemy.ext.asyncio import AsyncSession

    assert isinstance(session, AsyncSession)
    return KnowledgeExtractionService(
        versions=PostgresKnowledgeVersionRepository(session),
        chunks=PostgresChunkRepository(session),
        proposals=PostgresProposalRepository(session),
        runs=PostgresExtractionRunRepository(session),
        entities=PostgresEntityIndexRepository(session),
        llm=_llm_provider(),
        heuristic=HeuristicExtractor(),
        audit=PostgresAuditRepository(session),
        use_langgraph=True,
    )


async def _extract_pending() -> dict[str, int]:
    async with task_session() as session:
        service = _build_extraction_service(session)
        proposals = await service.process_pending(batch_size=BATCH_SIZE)
        approved = await _build_proposal_service(session).auto_approve_confident(
            OwnerContext(owner_id=DEFAULT_OWNER_ID),
            correlation_id=str(uuid4()),
        )
        remaining = await PostgresKnowledgeVersionRepository(session).count_pending_knowledge()

    if remaining > 0:
        enqueue_knowledge_extract_pending()
    if proposals > 0 or len(approved) > 0 or remaining == 0:
        enqueue_graph_projection_pending()

    logger.info(
        "knowledge_extract_pending_complete",
        proposals=proposals,
        auto_approved=len(approved),
        remaining_knowledge=remaining,
    )
    return {
        "proposals": proposals,
        "auto_approved": len(approved),
        "remaining": remaining,
    }


async def _extract_version(version_id: UUID) -> dict[str, int]:
    async with task_session() as session:
        service = _build_extraction_service(session)
        proposals = await service.extract_version(version_id)
        approved = await _build_proposal_service(session).auto_approve_confident(
            OwnerContext(owner_id=DEFAULT_OWNER_ID),
            correlation_id=str(uuid4()),
        )

    if proposals > 0 or len(approved) > 0:
        enqueue_graph_projection_pending()

    return {"proposals": proposals, "auto_approved": len(approved)}


@celery_app.task(name="worker.tasks.knowledge_extraction.extract_pending", bind=True)
def extract_pending(self: Task, **kwargs: object) -> dict[str, int]:
    logger.info("knowledge_extract_pending_started", task_id=self.request.id)
    return run_task(_extract_pending)


@celery_app.task(name="worker.tasks.knowledge_extraction.extract_version", bind=True)
def extract_version(self: Task, version_id: str, **kwargs: object) -> dict[str, int]:
    logger.info(
        "knowledge_extract_version_started",
        version_id=version_id,
        task_id=self.request.id,
    )
    return run_task(lambda: _extract_version(UUID(version_id)))
