from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ProjectSummaryItem(BaseModel):
    id: UUID
    name: str
    entity_type: str | None = None


class ProcessingHealth(BaseModel):
    sources_total: int = 0
    sources_enabled: int = 0
    pending_proposals: int = 0
    open_contradictions: int = 0
    pending_outbox_events: int = 0
    last_sync_at: datetime | None = None


class ProjectDashboard(BaseModel):
    summary: str
    projects: list[ProjectSummaryItem] = Field(default_factory=list)
    people: list[ProjectSummaryItem] = Field(default_factory=list)
    repositories: list[ProjectSummaryItem] = Field(default_factory=list)
    technologies: list[ProjectSummaryItem] = Field(default_factory=list)
    decisions: list[str] = Field(default_factory=list)
    open_tasks: list[str] = Field(default_factory=list)
    recent_events: list[str] = Field(default_factory=list)
    source_coverage: list[ProjectSummaryItem] = Field(default_factory=list)
    processing_health: ProcessingHealth = Field(default_factory=ProcessingHealth)


class StatusReportRequest(BaseModel):
    start_at: datetime | None = None
    end_at: datetime | None = None


class StatusReport(BaseModel):
    title: str
    period_start: datetime | None
    period_end: datetime | None
    summary: str
    decisions: list[str] = Field(default_factory=list)
    tasks: list[str] = Field(default_factory=list)
    events: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)
    citations: list[str] = Field(default_factory=list)
    generated_at: datetime
