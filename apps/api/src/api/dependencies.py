from collections.abc import AsyncIterator
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from adapters.connectors.google.factory import build_google_oauth
from adapters.connectors.google.oauth import GoogleOAuthService
from adapters.content.loader import LocalAndGitHubContentLoader
from adapters.embeddings.factory import build_embedding_provider
from adapters.graph.neo4j_repository import Neo4jGraphRepository
from adapters.llm.answer_synthesis import (
    HeuristicAnswerSynthesizer,
    OpenAICompatibleAnswerSynthesizer,
)
from adapters.parsers.factory import ParserFactory
from adapters.persistence.canonical_repository import (
    PostgresCanonicalRepository,
    PostgresOutboxRepository,
)
from adapters.persistence.chunk_repository import (
    PostgresChunkRepository,
    PostgresSourceProcessingStatsRepository,
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
from adapters.settings.config_loader import load_app_settings
from adapters.settings.resolver import ResolvedLlmSettings
from adapters.tasks.celery_dispatcher import CeleryTaskDispatcher
from application.canonical.materialization_service import CanonicalMaterializationService
from application.canonical.query_service import CanonicalQueryService, GraphQueryService
from application.content.preview import PreviewService
from application.content.search import SearchService
from application.knowledge.proposal_service import ProposalService
from application.operations.service import OperationsService
from application.policy import LocalPolicyService
from application.projects.dashboard_service import ProjectDashboardService
from application.projects.report_service import StatusReportService
from application.qa.answer_service import HybridRetrievalPlanner, QuestionAnsweringService
from application.qa.synthesis_service import AnswerSynthesisService
from application.sources.bootstrap_service import SourceBootstrapService
from application.sources.processing_stats_service import SourceProcessingStatsService
from application.sources.service import SourceRegistryService, SyncService
from domain.errors import DomainError
from domain.identity import OwnerContext
from fastapi import Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


@dataclass
class RequestServices:
    sources: SourceRegistryService
    sync: SyncService
    bootstrap: SourceBootstrapService
    search: SearchService
    preview: PreviewService
    proposals: ProposalService
    canonical: CanonicalQueryService
    graph: GraphQueryService
    qa: QuestionAnsweringService
    dashboard: ProjectDashboardService
    operations: OperationsService
    reports: StatusReportService
    processing_stats: SourceProcessingStatsService
    tasks: CeleryTaskDispatcher
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
    path_bridge: object,
    resolved_llm: ResolvedLlmSettings,
) -> RequestServices:
    sources_repo = PostgresSourceRepository(session)
    sync_repo = PostgresSyncRunRepository(session)
    audit_repo = PostgresAuditRepository(session)
    chunk_repo = PostgresChunkRepository(session)
    version_repo = PostgresVersionContentRepository(session)
    policy = LocalPolicyService()
    tasks = CeleryTaskDispatcher(broker_url)
    oauth = build_google_oauth(
        session=session,
        client_id=getattr(settings, "google_client_id", ""),
        client_secret=getattr(settings, "google_client_secret", ""),
        redirect_uri=getattr(settings, "google_redirect_uri", ""),
        session_secret=getattr(settings, "session_secret", ""),
        enabled=getattr(settings, "pkb_google_connectors_enabled", False),
    )
    embeddings = build_embedding_provider(resolved_llm)
    parser = ParserFactory()
    loader = LocalAndGitHubContentLoader(oauth_service=oauth)
    proposal_repo = PostgresProposalRepository(session)
    approval_repo = PostgresApprovalRepository(session)
    entity_repo = PostgresEntityIndexRepository(session)
    canonical_repo = PostgresCanonicalRepository(session)
    outbox_repo = PostgresOutboxRepository(session)
    materializer = CanonicalMaterializationService(canonical_repo, outbox_repo, entity_repo)
    graph_repo = Neo4jGraphRepository(settings)  # type: ignore[arg-type]
    search_service = SearchService(chunk_repo, embeddings, policy)
    graph_query = GraphQueryService(graph_repo, policy)
    heuristic = HeuristicAnswerSynthesizer()
    synthesizer = (
        OpenAICompatibleAnswerSynthesizer(resolved_llm, heuristic)
        if resolved_llm.llm_enabled
        else heuristic
    )
    planner_version = "graph_v2"
    synthesis_version = "graph_v2"
    config_path = getattr(settings, "settings_config_path", "config/settings.yaml")
    app_settings = load_app_settings(Path(config_path))
    if app_settings is not None:
        planner_version = app_settings.agents.planner.version
        synthesis_version = app_settings.agents.synthesis.version

    planner = HybridRetrievalPlanner(
        search_service,
        canonical_repo,
        graph_repo,
        policy,
        planner_version=planner_version,
    )
    bootstrap = SourceBootstrapService(sources_repo, audit_repo, path_bridge)
    processing_stats_repo = PostgresSourceProcessingStatsRepository(session)

    return RequestServices(
        sources=SourceRegistryService(sources_repo, audit_repo, policy),
        sync=SyncService(sources_repo, sync_repo, audit_repo, policy, tasks),
        bootstrap=bootstrap,
        search=search_service,
        preview=PreviewService(version_repo, chunk_repo, parser, loader, policy),
        proposals=ProposalService(
            proposal_repo,
            approval_repo,
            materializer,
            audit_repo,
            policy,
            on_materialized=tasks,
        ),
        canonical=CanonicalQueryService(canonical_repo, policy),
        graph=graph_query,
        qa=QuestionAnsweringService(
            planner,
            synthesizer,
            policy,
            audit=audit_repo,
            synthesis=AnswerSynthesisService(use_graph=synthesis_version == "graph_v2"),
        ),
        dashboard=ProjectDashboardService(canonical_repo, sources_repo, outbox_repo, policy),
        operations=OperationsService(canonical_repo, outbox_repo, policy),
        reports=StatusReportService(canonical_repo, policy),
        processing_stats=SourceProcessingStatsService(processing_stats_repo, policy),
        tasks=tasks,
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
        path_bridge=request.app.state.path_bridge,
        resolved_llm=request.app.state.resolved_llm_settings,
    )


def domain_error_response(exc: DomainError, correlation_id: str) -> dict[str, object]:
    return {
        "code": "domain_error",
        "message": str(exc),
        "details": {},
        "correlation_id": correlation_id,
    }


async def get_google_oauth(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> GoogleOAuthService:
    settings = request.app.state.settings
    return build_google_oauth(
        session=session,
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        redirect_uri=settings.google_redirect_uri,
        session_secret=settings.session_secret,
        enabled=settings.pkb_google_connectors_enabled,
    )
