from datetime import datetime
from uuid import UUID

from domain.sources import DEFAULT_EXCLUDE_GLOBS, SourceType
from domain.sync import SyncMode, SyncRunStatus
from pydantic import BaseModel, Field


class LocalSourceRequest(BaseModel):
    name: str
    path: str = ""
    paths: list[str] = Field(default_factory=list)
    file_extensions: list[str] = Field(default_factory=lambda: [".md", ".txt", ".pdf"])
    exclude_globs: list[str] = Field(default_factory=lambda: list(DEFAULT_EXCLUDE_GLOBS))
    default_project_id: UUID | None = None
    enabled: bool = True


class GitHubSourceRequest(BaseModel):
    name: str
    owner: str
    repo: str
    branch: str = "main"
    token_env_var: str = "GITHUB_TOKEN"
    default_project_id: UUID | None = None
    enabled: bool = True


class SourceResponse(BaseModel):
    id: UUID
    type: SourceType
    name: str
    owner_id: UUID
    configuration: dict[str, object]
    enabled: bool
    default_project_id: UUID | None


class SourceListResponse(BaseModel):
    items: list[SourceResponse]
    next_cursor: UUID | None = None


class StartSyncRequest(BaseModel):
    source_id: UUID
    mode: SyncMode = SyncMode.INCREMENTAL


class SyncRunResponse(BaseModel):
    id: UUID
    source_id: UUID
    mode: SyncMode
    status: SyncRunStatus
    correlation_id: str
    objects_discovered: int
    objects_processed: int
    objects_failed: int
    error_summary: str | None
    started_at: datetime | None
    completed_at: datetime | None


class SyncRunListResponse(BaseModel):
    items: list[SyncRunResponse]
    next_cursor: UUID | None = None
