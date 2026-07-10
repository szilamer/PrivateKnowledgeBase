from collections.abc import AsyncIterator
from dataclasses import dataclass
from uuid import uuid4

from adapters.content.loader import LocalAndGitHubContentLoader
from adapters.embeddings.openai_compatible import OpenAICompatibleEmbeddingProvider
from adapters.parsers.factory import ParserFactory
from adapters.persistence.chunk_repository import (
    PostgresChunkRepository,
    PostgresVersionContentRepository,
)
from adapters.persistence.knowledge_repository import (
    PostgresApprovalRepository,
    PostgresEntityIndexRepository,
    PostgresProposalRepository,
)
from adapters.persistence.repositories import (
    PostgresAuditRepository,
    PostgresSourceRepository,
    PostgresSyncRunRepository,
)
from adapters.persistence.session import session_scope
from adapters.tasks.celery_dispatcher import CeleryTaskDispatcher
from application.content.preview import PreviewService
from application.content.search import SearchService
from application.knowledge.proposal_service import ProposalService
from application.policy import LocalPolicyService
from application.sources.service import SourceRegistryService, SyncService
from domain.errors import DomainError
from domain.identity import OwnerContext
from fastapi import Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


@dataclass
class RequestServices:
    sources: SourceRegistryService
    sync: SyncService
    search: SearchService
    preview: PreviewService
    proposals: ProposalService
    owner: OwnerContext
    correlation_id: str


async def get_db_session(request: Request) -> AsyncIterator[AsyncSession]:
    factory: async_sessionmaker[AsyncSession] = request.app.state.session_factory
    async with session_scope(factory) as session:
        yield session


def build_services(
    session: AsyncSession,
    *,
    broker_url: str,
    settings: object,
    correlation_id: str,
) -> RequestServices:
    sources_repo = PostgresSourceRepository(session)
    sync_repo = PostgresSyncRunRepository(session)
    audit_repo = PostgresAuditRepository(session)
    chunk_repo = PostgresChunkRepository(session)
    version_repo = PostgresVersionContentRepository(session)
    policy = LocalPolicyService()
    tasks = CeleryTaskDispatcher(broker_url)
    embeddings = OpenAICompatibleEmbeddingProvider(settings)  # type: ignore[arg-type]
    parser = ParserFactory()
    loader = LocalAndGitHubContentLoader()
    proposal_repo = PostgresProposalRepository(session)
    approval_repo = PostgresApprovalRepository(session)
    entity_repo = PostgresEntityIndexRepository(session)

    return RequestServices(
        sources=SourceRegistryService(sources_repo, audit_repo, policy),
        sync=SyncService(sources_repo, sync_repo, audit_repo, policy, tasks),
        search=SearchService(chunk_repo, embeddings, policy),
        preview=PreviewService(version_repo, chunk_repo, parser, loader, policy),
        proposals=ProposalService(proposal_repo, approval_repo, entity_repo, audit_repo, policy),
        owner=OwnerContext(),
        correlation_id=correlation_id,
    )


async def get_services(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    x_correlation_id: str | None = Header(default=None),
) -> AsyncIterator[RequestServices]:
    correlation_id = x_correlation_id or str(uuid4())
    settings = request.app.state.settings
    yield build_services(
        session,
        broker_url=settings.celery_broker_url,
        settings=settings,
        correlation_id=correlation_id,
    )


def domain_error_response(exc: DomainError, correlation_id: str) -> dict[str, object]:
    return {
        "code": "domain_error",
        "message": str(exc),
        "details": {},
        "correlation_id": correlation_id,
    }
