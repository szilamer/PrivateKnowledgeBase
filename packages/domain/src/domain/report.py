from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field

PROJECT_REPORT_PIPELINE_VERSION = "v1"


class ProjectReportStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ProjectReportRequest(BaseModel):
    project_entity_id: UUID
    start_at: datetime | None = None
    end_at: datetime | None = None


class ProjectSubgraphData(BaseModel):
    project_name: str
    decisions: list[str] = Field(default_factory=list)
    tasks: list[str] = Field(default_factory=list)
    events: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)
    citations: list[str] = Field(default_factory=list)


class ProjectReportArtifact(BaseModel):
    id: UUID
    owner_id: UUID
    project_entity_id: UUID
    status: ProjectReportStatus
    title: str
    markdown: str | None = None
    citations: list[str] = Field(default_factory=list)
    provenance: dict[str, object] = Field(default_factory=dict)
    period_start: datetime | None = None
    period_end: datetime | None = None
    error_summary: str | None = None
    created_at: datetime
    completed_at: datetime | None = None
