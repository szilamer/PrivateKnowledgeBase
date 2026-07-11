import json
from datetime import UTC, datetime
from uuid import UUID, uuid4

from domain.audit import AuditEvent
from domain.sources import Source, SourceType
from domain.sync import (
    DiscoveredObject,
    ExtractionStatus,
    SourceObject,
    SourceObjectVersion,
    SyncRun,
    SyncRunStatus,
)
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


def _parse_source(row: object) -> Source:
    mapping = dict(row._mapping)  # type: ignore[attr-defined]
    return Source(
        id=mapping["id"],
        type=SourceType(mapping["type"]),
        name=mapping["name"],
        owner_id=mapping["owner_id"],
        configuration=mapping["configuration"],
        enabled=mapping["enabled"],
        default_project_id=mapping["default_project_id"],
    )


def _parse_sync_run(row: object) -> SyncRun:
    from domain.sync import SyncMode, SyncRunStatus

    mapping = dict(row._mapping)  # type: ignore[attr-defined]
    return SyncRun(
        id=mapping["id"],
        source_id=mapping["source_id"],
        mode=SyncMode(mapping["mode"]),
        status=SyncRunStatus(mapping["status"]),
        correlation_id=mapping["correlation_id"],
        idempotency_key=mapping["idempotency_key"],
        objects_discovered=mapping["objects_discovered"],
        objects_processed=mapping["objects_processed"],
        objects_failed=mapping["objects_failed"],
        error_summary=mapping["error_summary"],
        started_at=mapping["started_at"],
        completed_at=mapping["completed_at"],
    )


class PostgresSourceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, source: Source) -> Source:
        await self._session.execute(
            text(
                """
                INSERT INTO sources (
                    id, type, name, owner_id, configuration, enabled, default_project_id
                ) VALUES (
                    :id, :type, :name, :owner_id,
                    CAST(:configuration AS jsonb), :enabled, :default_project_id
                )
                """
            ),
            {
                "id": source.id,
                "type": source.type.value,
                "name": source.name,
                "owner_id": source.owner_id,
                "configuration": json.dumps(source.configuration),
                "enabled": source.enabled,
                "default_project_id": source.default_project_id,
            },
        )
        return source

    async def upsert(self, source: Source) -> Source:
        existing = await self.get_by_id(source.id, source.owner_id)
        if existing is None:
            return await self.create(source)
        await self._session.execute(
            text(
                """
                UPDATE sources
                SET type = :type,
                    name = :name,
                    configuration = CAST(:configuration AS jsonb),
                    enabled = :enabled,
                    default_project_id = :default_project_id,
                    updated_at = NOW()
                WHERE id = :id AND owner_id = :owner_id
                """
            ),
            {
                "id": source.id,
                "owner_id": source.owner_id,
                "type": source.type.value,
                "name": source.name,
                "configuration": json.dumps(source.configuration),
                "enabled": source.enabled,
                "default_project_id": source.default_project_id,
            },
        )
        return source

    async def get_by_id(self, source_id: UUID, owner_id: UUID) -> Source | None:
        result = await self._session.execute(
            text("SELECT * FROM sources WHERE id = :id AND owner_id = :owner_id"),
            {"id": source_id, "owner_id": owner_id},
        )
        row = result.first()
        return _parse_source(row) if row else None

    async def get_by_id_unscoped(self, source_id: UUID) -> Source | None:
        result = await self._session.execute(
            text("SELECT * FROM sources WHERE id = :id"),
            {"id": source_id},
        )
        row = result.first()
        return _parse_source(row) if row else None

    async def list_by_owner(
        self, owner_id: UUID, *, limit: int, cursor: UUID | None
    ) -> tuple[list[Source], UUID | None]:
        query = """
            SELECT * FROM sources
            WHERE owner_id = :owner_id
        """
        params: dict[str, object] = {"owner_id": owner_id, "limit": limit + 1}
        if cursor:
            query += " AND id > :cursor"
            params["cursor"] = cursor
        query += " ORDER BY id LIMIT :limit"
        result = await self._session.execute(text(query), params)
        rows = result.fetchall()
        sources = [_parse_source(row) for row in rows[:limit]]
        next_cursor = rows[limit].id if len(rows) > limit else None
        return sources, next_cursor

    async def delete(self, source_id: UUID, owner_id: UUID) -> bool:
        existing = await self.get_by_id(source_id, owner_id)
        if existing is None:
            return False
        await self._session.execute(
            text(
                """
                DELETE FROM source_object_versions
                WHERE source_object_id IN (
                    SELECT id FROM source_objects WHERE source_id = :source_id
                )
                """
            ),
            {"source_id": source_id},
        )
        await self._session.execute(
            text("DELETE FROM source_objects WHERE source_id = :source_id"),
            {"source_id": source_id},
        )
        await self._session.execute(
            text("DELETE FROM sync_runs WHERE source_id = :source_id"),
            {"source_id": source_id},
        )
        await self._session.execute(
            text("DELETE FROM sources WHERE id = :id AND owner_id = :owner_id"),
            {"id": source_id, "owner_id": owner_id},
        )
        return (await self.get_by_id(source_id, owner_id)) is None


class PostgresSyncRunRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, sync_run: SyncRun) -> SyncRun:
        await self._session.execute(
            text(
                """
                INSERT INTO sync_runs (
                    id, source_id, mode, status, correlation_id, idempotency_key,
                    objects_discovered, objects_processed, objects_failed,
                    error_summary, started_at, completed_at
                ) VALUES (
                    :id, :source_id, :mode, :status, :correlation_id, :idempotency_key,
                    :objects_discovered, :objects_processed, :objects_failed,
                    :error_summary, :started_at, :completed_at
                )
                """
            ),
            {
                "id": sync_run.id,
                "source_id": sync_run.source_id,
                "mode": sync_run.mode.value,
                "status": sync_run.status.value,
                "correlation_id": sync_run.correlation_id,
                "idempotency_key": sync_run.idempotency_key,
                "objects_discovered": sync_run.objects_discovered,
                "objects_processed": sync_run.objects_processed,
                "objects_failed": sync_run.objects_failed,
                "error_summary": sync_run.error_summary,
                "started_at": sync_run.started_at,
                "completed_at": sync_run.completed_at,
            },
        )
        return sync_run

    async def get_by_id(self, sync_run_id: UUID) -> SyncRun | None:
        result = await self._session.execute(
            text("SELECT * FROM sync_runs WHERE id = :id"),
            {"id": sync_run_id},
        )
        row = result.first()
        return _parse_sync_run(row) if row else None

    async def get_by_idempotency_key(self, source_id: UUID, idempotency_key: str) -> SyncRun | None:
        result = await self._session.execute(
            text(
                """
                SELECT * FROM sync_runs
                WHERE source_id = :source_id AND idempotency_key = :idempotency_key
                """
            ),
            {"source_id": source_id, "idempotency_key": idempotency_key},
        )
        row = result.first()
        return _parse_sync_run(row) if row else None

    async def update(self, sync_run: SyncRun) -> SyncRun:
        await self._session.execute(
            text(
                """
                UPDATE sync_runs SET
                    status = :status,
                    objects_discovered = :objects_discovered,
                    objects_processed = :objects_processed,
                    objects_failed = :objects_failed,
                    error_summary = :error_summary,
                    started_at = :started_at,
                    completed_at = :completed_at
                WHERE id = :id
                """
            ),
            {
                "id": sync_run.id,
                "status": sync_run.status.value,
                "objects_discovered": sync_run.objects_discovered,
                "objects_processed": sync_run.objects_processed,
                "objects_failed": sync_run.objects_failed,
                "error_summary": sync_run.error_summary,
                "started_at": sync_run.started_at,
                "completed_at": sync_run.completed_at,
            },
        )
        return sync_run

    async def list_by_source(
        self, source_id: UUID, *, limit: int, cursor: UUID | None
    ) -> tuple[list[SyncRun], UUID | None]:
        query = "SELECT * FROM sync_runs WHERE source_id = :source_id"
        params: dict[str, object] = {"source_id": source_id, "limit": limit + 1}
        if cursor:
            query += " AND id < :cursor"
            params["cursor"] = cursor
        query += " ORDER BY id DESC LIMIT :limit"
        result = await self._session.execute(text(query), params)
        rows = result.fetchall()
        runs = [_parse_sync_run(row) for row in rows[:limit]]
        next_cursor = rows[limit].id if len(rows) > limit else None
        return runs, next_cursor

    async def list_by_status(self, status: SyncRunStatus, *, limit: int = 100) -> list[SyncRun]:
        result = await self._session.execute(
            text(
                """
                SELECT * FROM sync_runs
                WHERE status = :status
                ORDER BY id
                LIMIT :limit
                """
            ),
            {"status": status.value, "limit": limit},
        )
        return [_parse_sync_run(row) for row in result.fetchall()]


class PostgresSourceObjectRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert_object(
        self, source_id: UUID, external_id: str, object_type: str
    ) -> SourceObject:
        object_id = uuid4()
        await self._session.execute(
            text(
                """
                INSERT INTO source_objects (id, source_id, external_id, object_type)
                VALUES (:id, :source_id, :external_id, :object_type)
                ON CONFLICT (source_id, external_id) DO NOTHING
                """
            ),
            {
                "id": object_id,
                "source_id": source_id,
                "external_id": external_id,
                "object_type": object_type,
            },
        )
        result = await self._session.execute(
            text(
                """
                SELECT id, source_id, external_id, object_type
                FROM source_objects
                WHERE source_id = :source_id AND external_id = :external_id
                """
            ),
            {"source_id": source_id, "external_id": external_id},
        )
        row = result.one()
        return SourceObject(
            id=row.id,
            source_id=row.source_id,
            external_id=row.external_id,
            object_type=row.object_type,
        )

    async def get_latest_version_hash(
        self, source_object_id: UUID, pipeline_version: str
    ) -> str | None:
        result = await self._session.execute(
            text(
                """
                SELECT content_hash FROM source_object_versions
                WHERE source_object_id = :source_object_id
                  AND pipeline_version = :pipeline_version
                ORDER BY observed_at DESC
                LIMIT 1
                """
            ),
            {
                "source_object_id": source_object_id,
                "pipeline_version": pipeline_version,
            },
        )
        row = result.first()
        return row.content_hash if row else None

    async def create_version_if_changed(
        self,
        source_object_id: UUID,
        discovered: DiscoveredObject,
        pipeline_version: str,
    ) -> SourceObjectVersion | None:
        latest = await self.get_latest_version_hash(source_object_id, pipeline_version)
        if latest == discovered.content_hash:
            return None

        version = SourceObjectVersion(
            id=uuid4(),
            source_object_id=source_object_id,
            content_hash=discovered.content_hash,
            mime_type=discovered.mime_type,
            observed_at=datetime.now(UTC),
            extraction_status=ExtractionStatus.PENDING,
            content_ref=discovered.content_ref,
            pipeline_version=pipeline_version,
        )
        await self._session.execute(
            text(
                """
                INSERT INTO source_object_versions (
                    id, source_object_id, content_hash, mime_type, observed_at,
                    extraction_status, content_ref, pipeline_version
                ) VALUES (
                    :id, :source_object_id, :content_hash, :mime_type, :observed_at,
                    :extraction_status, :content_ref, :pipeline_version
                )
                ON CONFLICT (source_object_id, content_hash, pipeline_version) DO NOTHING
                """
            ),
            {
                "id": version.id,
                "source_object_id": version.source_object_id,
                "content_hash": version.content_hash,
                "mime_type": version.mime_type,
                "observed_at": version.observed_at,
                "extraction_status": version.extraction_status.value,
                "content_ref": version.content_ref,
                "pipeline_version": version.pipeline_version,
            },
        )
        return version


class PostgresAuditRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def append(self, event: AuditEvent) -> None:
        await self._session.execute(
            text(
                """
                INSERT INTO audit_events (
                    id, actor_id, action, object_type, object_id,
                    correlation_id, metadata, created_at
                ) VALUES (
                    :id, :actor_id, :action, :object_type, :object_id,
                    :correlation_id, CAST(:metadata AS jsonb), :created_at
                )
                """
            ),
            {
                "id": event.id,
                "actor_id": event.actor_id,
                "action": event.action.value,
                "object_type": event.object_type,
                "object_id": event.object_id,
                "correlation_id": event.correlation_id,
                "metadata": json.dumps(event.metadata),
                "created_at": event.created_at,
            },
        )
