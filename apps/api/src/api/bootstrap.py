from pathlib import Path

from adapters.persistence.repositories import (
    PostgresAuditRepository,
    PostgresSourceRepository,
    PostgresSyncRunRepository,
)
from adapters.persistence.session import session_scope
from adapters.tasks.celery_dispatcher import CeleryTaskDispatcher
from application.policy import LocalPolicyService
from application.sources.bootstrap_service import SourceBootstrapService
from application.sources.config_service import SourceConfigService
from application.sources.service import SyncService
from domain.identity import OwnerContext
from domain.sync import SyncMode


async def bootstrap_sources(app: object) -> None:
    settings = app.state.settings  # type: ignore[attr-defined]
    config_service = SourceConfigService(Path(settings.sources_config_path))
    config = config_service.get_config()
    if not config.sources:
        return

    factory = app.state.session_factory  # type: ignore[attr-defined]
    bridge = app.state.path_bridge  # type: ignore[attr-defined]
    tasks = CeleryTaskDispatcher(settings.celery_broker_url)
    policy = LocalPolicyService()
    owner = OwnerContext()

    async with session_scope(factory) as session:
        sources_repo = PostgresSourceRepository(session)
        audit_repo = PostgresAuditRepository(session)
        sync_repo = PostgresSyncRunRepository(session)
        bootstrap = SourceBootstrapService(sources_repo, audit_repo, bridge)
        upserted = await bootstrap.apply_config(config, correlation_id="startup-bootstrap")
        if not config.sync.on_startup:
            return
        sync_service = SyncService(sources_repo, sync_repo, audit_repo, policy, tasks)
        for source in upserted:
            if source.enabled:
                await sync_service.start_sync(
                    owner,
                    source.id,
                    SyncMode.INCREMENTAL,
                    correlation_id="startup-bootstrap",
                    idempotency_key=f"bootstrap:{source.configuration.get('config_id')}",
                )
