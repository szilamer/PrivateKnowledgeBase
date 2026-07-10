from datetime import datetime
from uuid import uuid4

from application.ports import AuditRepository, SourceRepository
from domain.audit import AuditAction, AuditEvent
from domain.identity import DEFAULT_OWNER_ID
from domain.source_config import (
    GmailSourceConfig,
    GoogleCalendarSourceConfig,
    GoogleDriveSourceConfig,
    LocalFolderSourceConfig,
    SourceEntryConfig,
    SourcesFileConfig,
)
from domain.sources import Source, SourceType, source_id_for_config


class SourceBootstrapService:
    """FR-SRC-010 — upsert declarative sources from config/sources.yaml."""

    def __init__(
        self,
        sources: SourceRepository,
        audit: AuditRepository,
        path_bridge: object,
    ) -> None:
        self._sources = sources
        self._audit = audit
        self._path_bridge = path_bridge

    async def apply_config(
        self,
        config: SourcesFileConfig,
        *,
        correlation_id: str = "bootstrap",
    ) -> list[Source]:
        upserted: list[Source] = []
        for entry in config.sources:
            source = _entry_to_source(entry, self._path_bridge)
            saved = await self._sources.upsert(source)
            upserted.append(saved)
            await self._audit.append(
                AuditEvent(
                    id=uuid4(),
                    actor_id=DEFAULT_OWNER_ID,
                    action=AuditAction.SOURCE_REGISTERED,
                    object_type="source",
                    object_id=saved.id,
                    correlation_id=correlation_id,
                    metadata={
                        "type": saved.type.value,
                        "name": saved.name,
                        "config_id": entry.id,
                        "bootstrap": True,
                    },
                    created_at=_utcnow(),
                )
            )
        return upserted


def _entry_to_source(entry: SourceEntryConfig, path_bridge: object) -> Source:
    resolve_many = getattr(path_bridge, "resolve_many", None)
    if isinstance(entry, LocalFolderSourceConfig):
        host_paths = list(entry.paths)
        container_paths = resolve_many(host_paths) if resolve_many else host_paths
        configuration: dict[str, object] = {
            "config_id": entry.id,
            "paths": container_paths,
            "host_paths": host_paths,
            "file_extensions": entry.include_extensions,
            "exclude_globs": entry.exclude_globs,
        }
        return Source(
            id=source_id_for_config(entry.id),
            type=SourceType.LOCAL_FOLDER,
            name=entry.name,
            owner_id=DEFAULT_OWNER_ID,
            configuration=configuration,
            enabled=entry.enabled,
        )
    if isinstance(entry, GoogleDriveSourceConfig):
        return Source(
            id=source_id_for_config(entry.id),
            type=SourceType.GOOGLE_DRIVE,
            name=entry.name,
            owner_id=DEFAULT_OWNER_ID,
            configuration={
                "config_id": entry.id,
                "account": entry.account,
                "folder_ids": entry.folder_ids,
                "include_google_docs": entry.include_google_docs,
                "include_extensions": entry.include_extensions,
            },
            enabled=entry.enabled,
        )
    if isinstance(entry, GmailSourceConfig):
        return Source(
            id=source_id_for_config(entry.id),
            type=SourceType.GMAIL,
            name=entry.name,
            owner_id=DEFAULT_OWNER_ID,
            configuration={
                "config_id": entry.id,
                "account": entry.account,
                "query": entry.query,
                "label_ids": entry.label_ids,
                "include_attachments": entry.include_attachments,
                "attachment_extensions": entry.attachment_extensions,
            },
            enabled=entry.enabled,
        )
    if isinstance(entry, GoogleCalendarSourceConfig):
        return Source(
            id=source_id_for_config(entry.id),
            type=SourceType.GOOGLE_CALENDAR,
            name=entry.name,
            owner_id=DEFAULT_OWNER_ID,
            configuration={
                "config_id": entry.id,
                "account": entry.account,
                "calendar_ids": entry.calendar_ids,
                "horizon_past_days": entry.horizon_past_days,
                "horizon_future_days": entry.horizon_future_days,
            },
            enabled=entry.enabled,
        )
    msg = f"Unsupported source config type: {entry}"
    raise ValueError(msg)


def _utcnow() -> datetime:
    from datetime import UTC, datetime

    return datetime.now(UTC)
