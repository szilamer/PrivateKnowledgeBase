from typing import Protocol
from uuid import UUID

from domain.audit import AuditEvent
from domain.identity import OwnerContext
from domain.sources import Source
from domain.sync import DiscoveredObject, SourceObject, SourceObjectVersion, SyncRun


class SourceRepository(Protocol):
    async def create(self, source: Source) -> Source: ...

    async def get_by_id(self, source_id: UUID, owner_id: UUID) -> Source | None: ...

    async def get_by_id_unscoped(self, source_id: UUID) -> Source | None: ...

    async def list_by_owner(
        self, owner_id: UUID, *, limit: int, cursor: UUID | None
    ) -> tuple[list[Source], UUID | None]: ...


class SyncRunRepository(Protocol):
    async def create(self, sync_run: SyncRun) -> SyncRun: ...

    async def get_by_id(self, sync_run_id: UUID) -> SyncRun | None: ...

    async def get_by_idempotency_key(
        self, source_id: UUID, idempotency_key: str
    ) -> SyncRun | None: ...

    async def update(self, sync_run: SyncRun) -> SyncRun: ...

    async def list_by_source(
        self, source_id: UUID, *, limit: int, cursor: UUID | None
    ) -> tuple[list[SyncRun], UUID | None]: ...


class SourceObjectRepository(Protocol):
    async def upsert_object(
        self, source_id: UUID, external_id: str, object_type: str
    ) -> SourceObject: ...

    async def get_latest_version_hash(
        self, source_object_id: UUID, pipeline_version: str
    ) -> str | None: ...

    async def create_version_if_changed(
        self,
        source_object_id: UUID,
        discovered: DiscoveredObject,
        pipeline_version: str,
    ) -> SourceObjectVersion | None: ...


class AuditRepository(Protocol):
    async def append(self, event: AuditEvent) -> None: ...


class SourceConnector(Protocol):
    async def discover(self, source: Source) -> list[DiscoveredObject]: ...


class TaskDispatcher(Protocol):
    async def enqueue_sync_run(self, sync_run_id: UUID) -> None: ...


class PolicyService(Protocol):
    def authorize_owner(self, ctx: OwnerContext, owner_id: UUID) -> None: ...
