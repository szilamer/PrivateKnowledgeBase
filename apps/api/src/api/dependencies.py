from collections.abc import AsyncIterator
from dataclasses import dataclass
from uuid import uuid4

from adapters.persistence.repositories import (
    PostgresAuditRepository,
    PostgresSourceRepository,
    PostgresSyncRunRepository,
)
from adapters.persistence.session import session_scope
from adapters.tasks.celery_dispatcher import CeleryTaskDispatcher
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
    correlation_id: str,
) -> RequestServices:
    sources_repo = PostgresSourceRepository(session)
    sync_repo = PostgresSyncRunRepository(session)
    audit_repo = PostgresAuditRepository(session)
    policy = LocalPolicyService()
    tasks = CeleryTaskDispatcher(broker_url)

    return RequestServices(
        sources=SourceRegistryService(sources_repo, audit_repo, policy),
        sync=SyncService(sources_repo, sync_repo, audit_repo, policy, tasks),
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
        correlation_id=correlation_id,
    )


def domain_error_response(exc: DomainError, correlation_id: str) -> dict[str, object]:
    return {
        "code": "domain_error",
        "message": str(exc),
        "details": {},
        "correlation_id": correlation_id,
    }
