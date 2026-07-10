from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel


class SyncMode(StrEnum):
    FULL = "full"
    INCREMENTAL = "incremental"


class SyncRunStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"


class ExtractionStatus(StrEnum):
    PENDING = "pending"
    SKIPPED = "skipped"
    COMPLETED = "completed"
    FAILED = "failed"


class SyncRun(BaseModel):
    id: UUID
    source_id: UUID
    mode: SyncMode
    status: SyncRunStatus
    correlation_id: str
    idempotency_key: str | None = None
    objects_discovered: int = 0
    objects_processed: int = 0
    objects_failed: int = 0
    error_summary: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class SourceObject(BaseModel):
    id: UUID
    source_id: UUID
    external_id: str
    object_type: str = "file"


class SourceObjectVersion(BaseModel):
    id: UUID
    source_object_id: UUID
    content_hash: str
    mime_type: str | None = None
    observed_at: datetime
    extraction_status: ExtractionStatus = ExtractionStatus.PENDING
    content_ref: str | None = None
    pipeline_version: str = "0.1.0"


class DiscoveredObject(BaseModel):
    external_id: str
    object_type: str = "file"
    content_hash: str
    mime_type: str | None = None
    content_ref: str | None = None


class SyncProgress(BaseModel):
    sync_run_id: UUID
    status: SyncRunStatus
    objects_discovered: int = 0
    objects_processed: int = 0
    objects_failed: int = 0
    error_summary: str | None = None
