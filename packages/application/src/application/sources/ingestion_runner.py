from datetime import datetime
from uuid import UUID, uuid4

from application.ports import (
    AuditRepository,
    SourceConnector,
    SourceObjectRepository,
    SourceRepository,
    SyncRunRepository,
)
from domain.audit import AuditAction, AuditEvent
from domain.sync import SyncMode, SyncRun, SyncRunStatus


class IngestionRunner:
    """FR-ING-001/002/003/004 — execute sync run against a connector."""

    PIPELINE_VERSION = "0.1.0"

    def __init__(
        self,
        sources: SourceRepository,
        sync_runs: SyncRunRepository,
        objects: SourceObjectRepository,
        audit: AuditRepository,
        connector: SourceConnector,
    ) -> None:
        self._sources = sources
        self._sync_runs = sync_runs
        self._objects = objects
        self._audit = audit
        self._connector = connector

    async def run(self, sync_run_id: UUID) -> SyncRun:
        sync_run = await self._sync_runs.get_by_id(sync_run_id)
        if sync_run is None:
            msg = f"Sync run not found: {sync_run_id}"
            raise ValueError(msg)

        source = await self._sources.get_by_id_unscoped(sync_run.source_id)
        if source is None:
            await self._fail(sync_run, "Source not found")
            result = await self._sync_runs.get_by_id(sync_run_id)
            assert result is not None
            return result

        sync_run.status = SyncRunStatus.RUNNING
        sync_run.started_at = _utcnow()
        await self._sync_runs.update(sync_run)

        try:
            discovered = await self._connector.discover(source)
        except Exception as exc:  # noqa: BLE001 — record sync failure
            await self._fail(sync_run, str(exc))
            result = await self._sync_runs.get_by_id(sync_run_id)
            assert result is not None
            return result

        sync_run.objects_discovered = len(discovered)
        processed = 0
        failed = 0
        errors: list[str] = []

        for item in discovered:
            try:
                obj = await self._objects.upsert_object(
                    source.id, item.external_id, item.object_type
                )
                if sync_run.mode == SyncMode.INCREMENTAL:
                    latest = await self._objects.get_latest_version_hash(
                        obj.id, self.PIPELINE_VERSION
                    )
                    if latest == item.content_hash:
                        processed += 1
                        continue

                version = await self._objects.create_version_if_changed(
                    obj.id, item, self.PIPELINE_VERSION
                )
                _ = version
                processed += 1
            except Exception as exc:  # noqa: BLE001 — FR-ING-004 partial failure
                failed += 1
                errors.append(f"{item.external_id}: {exc}")

        sync_run.objects_processed = processed
        sync_run.objects_failed = failed
        sync_run.completed_at = _utcnow()
        if failed and processed:
            sync_run.status = SyncRunStatus.PARTIAL
            sync_run.error_summary = "; ".join(errors[:5])
        elif failed:
            sync_run.status = SyncRunStatus.FAILED
            sync_run.error_summary = "; ".join(errors[:5])
        else:
            sync_run.status = SyncRunStatus.COMPLETED

        updated = await self._sync_runs.update(sync_run)
        await self._audit.append(
            AuditEvent(
                id=uuid4(),
                actor_id=source.owner_id,
                action=(
                    AuditAction.SYNC_COMPLETED
                    if updated.status in {SyncRunStatus.COMPLETED, SyncRunStatus.PARTIAL}
                    else AuditAction.SYNC_FAILED
                ),
                object_type="sync_run",
                object_id=updated.id,
                correlation_id=updated.correlation_id,
                metadata={
                    "objects_discovered": updated.objects_discovered,
                    "objects_processed": updated.objects_processed,
                    "objects_failed": updated.objects_failed,
                },
                created_at=_utcnow(),
            )
        )
        return updated

    async def _fail(self, sync_run: SyncRun, message: str) -> None:
        sync_run.status = SyncRunStatus.FAILED
        sync_run.error_summary = message
        sync_run.completed_at = _utcnow()
        await self._sync_runs.update(sync_run)


def _utcnow() -> datetime:
    from datetime import UTC, datetime

    return datetime.now(UTC)
