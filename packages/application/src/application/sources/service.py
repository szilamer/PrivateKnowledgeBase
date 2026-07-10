from datetime import datetime
from uuid import UUID, uuid4

from application.ports import (
    AuditRepository,
    PolicyService,
    SourceRepository,
    SyncRunRepository,
    TaskDispatcher,
)
from domain.audit import AuditAction, AuditEvent
from domain.errors import DomainError
from domain.identity import DEFAULT_OWNER_ID, OwnerContext
from domain.sources import (
    RegisterGitHubSourceCommand,
    RegisterLocalSourceCommand,
    Source,
    SourceType,
)
from domain.sync import SyncMode, SyncRun, SyncRunStatus


class SourceRegistryService:
    """MVP-01 / FR-SRC-001, FR-SRC-002 — register and list sources."""

    def __init__(
        self,
        sources: SourceRepository,
        audit: AuditRepository,
        policy: PolicyService,
    ) -> None:
        self._sources = sources
        self._audit = audit
        self._policy = policy

    async def register_local(
        self,
        ctx: OwnerContext,
        command: RegisterLocalSourceCommand,
        *,
        correlation_id: str,
        host_paths: list[str] | None = None,
    ) -> Source:
        self._policy.authorize_owner(ctx, DEFAULT_OWNER_ID)
        paths = list(command.paths)
        if command.path.strip():
            paths.append(command.path.strip())
        if not paths:
            raise DomainError("At least one local folder path is required")

        display_paths = list(host_paths) if host_paths else paths
        source = Source(
            id=uuid4(),
            type=SourceType.LOCAL_FOLDER,
            name=command.name,
            owner_id=DEFAULT_OWNER_ID,
            configuration={
                "paths": paths,
                "host_paths": display_paths,
                "file_extensions": command.file_extensions,
                "exclude_globs": command.exclude_globs,
            },
            enabled=command.enabled,
            default_project_id=command.default_project_id,
        )
        created = await self._sources.create(source)
        await self._audit.append(
            AuditEvent(
                id=uuid4(),
                actor_id=ctx.owner_id,
                action=AuditAction.SOURCE_REGISTERED,
                object_type="source",
                object_id=created.id,
                correlation_id=correlation_id,
                metadata={"type": created.type.value, "name": created.name},
                created_at=_utcnow(),
            )
        )
        return created

    async def register_github(
        self,
        ctx: OwnerContext,
        command: RegisterGitHubSourceCommand,
        *,
        correlation_id: str,
    ) -> Source:
        self._policy.authorize_owner(ctx, DEFAULT_OWNER_ID)
        source = Source(
            id=uuid4(),
            type=SourceType.GITHUB,
            name=command.name,
            owner_id=DEFAULT_OWNER_ID,
            configuration={
                "owner": command.owner,
                "repo": command.repo,
                "branch": command.branch,
                "token_env_var": command.token_env_var,
            },
            enabled=command.enabled,
            default_project_id=command.default_project_id,
        )
        created = await self._sources.create(source)
        await self._audit.append(
            AuditEvent(
                id=uuid4(),
                actor_id=ctx.owner_id,
                action=AuditAction.SOURCE_REGISTERED,
                object_type="source",
                object_id=created.id,
                correlation_id=correlation_id,
                metadata={
                    "type": created.type.value,
                    "name": created.name,
                    "repo": f"{command.owner}/{command.repo}",
                },
                created_at=_utcnow(),
            )
        )
        return created

    async def list_sources(
        self,
        ctx: OwnerContext,
        *,
        limit: int = 50,
        cursor: UUID | None = None,
    ) -> tuple[list[Source], UUID | None]:
        self._policy.authorize_owner(ctx, DEFAULT_OWNER_ID)
        return await self._sources.list_by_owner(DEFAULT_OWNER_ID, limit=limit, cursor=cursor)

    async def get_source(self, ctx: OwnerContext, source_id: UUID) -> Source:
        self._policy.authorize_owner(ctx, DEFAULT_OWNER_ID)
        source = await self._sources.get_by_id(source_id, DEFAULT_OWNER_ID)
        if source is None:
            raise DomainError(f"Source not found: {source_id}")
        return source


class SyncService:
    """MVP-02 / FR-ING-001, FR-ING-002 — start and track synchronization runs."""

    def __init__(
        self,
        sources: SourceRepository,
        sync_runs: SyncRunRepository,
        audit: AuditRepository,
        policy: PolicyService,
        tasks: TaskDispatcher,
    ) -> None:
        self._sources = sources
        self._sync_runs = sync_runs
        self._audit = audit
        self._policy = policy
        self._tasks = tasks

    async def start_sync(
        self,
        ctx: OwnerContext,
        source_id: UUID,
        mode: SyncMode,
        *,
        correlation_id: str,
        idempotency_key: str | None = None,
    ) -> SyncRun:
        self._policy.authorize_owner(ctx, DEFAULT_OWNER_ID)
        source = await self._sources.get_by_id(source_id, DEFAULT_OWNER_ID)
        if source is None:
            raise DomainError(f"Source not found: {source_id}")
        if not source.enabled:
            raise DomainError("Source is disabled")

        if idempotency_key:
            existing = await self._sync_runs.get_by_idempotency_key(source_id, idempotency_key)
            if existing is not None:
                return existing

        sync_run = SyncRun(
            id=uuid4(),
            source_id=source_id,
            mode=mode,
            status=SyncRunStatus.PENDING,
            correlation_id=correlation_id,
            idempotency_key=idempotency_key,
        )
        created = await self._sync_runs.create(sync_run)
        await self._audit.append(
            AuditEvent(
                id=uuid4(),
                actor_id=ctx.owner_id,
                action=AuditAction.SYNC_STARTED,
                object_type="sync_run",
                object_id=created.id,
                correlation_id=correlation_id,
                metadata={"source_id": str(source_id), "mode": mode.value},
                created_at=_utcnow(),
            )
        )
        await self._tasks.enqueue_sync_run(created.id)
        return created

    async def get_sync_run(self, ctx: OwnerContext, sync_run_id: UUID) -> SyncRun:
        self._policy.authorize_owner(ctx, DEFAULT_OWNER_ID)
        sync_run = await self._sync_runs.get_by_id(sync_run_id)
        if sync_run is None:
            raise DomainError(f"Sync run not found: {sync_run_id}")
        return sync_run

    async def list_sync_runs(
        self,
        ctx: OwnerContext,
        source_id: UUID,
        *,
        limit: int = 50,
        cursor: UUID | None = None,
    ) -> tuple[list[SyncRun], UUID | None]:
        self._policy.authorize_owner(ctx, DEFAULT_OWNER_ID)
        source = await self._sources.get_by_id(source_id, DEFAULT_OWNER_ID)
        if source is None:
            raise DomainError(f"Source not found: {source_id}")
        return await self._sync_runs.list_by_source(source_id, limit=limit, cursor=cursor)


def _utcnow() -> datetime:
    from datetime import UTC, datetime

    return datetime.now(UTC)
