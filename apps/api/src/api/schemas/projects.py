from datetime import datetime

from pydantic import BaseModel, Field


class ProjectSummaryItemResponse(BaseModel):
    id: str
    name: str
    entity_type: str | None = None


class ProcessingHealthResponse(BaseModel):
    sources_total: int
    sources_enabled: int
    pending_proposals: int = 0
    open_contradictions: int
    pending_outbox_events: int
    last_sync_at: datetime | None = None


class ProjectDashboardResponse(BaseModel):
    summary: str
    projects: list[ProjectSummaryItemResponse] = Field(default_factory=list)
    people: list[ProjectSummaryItemResponse] = Field(default_factory=list)
    repositories: list[ProjectSummaryItemResponse] = Field(default_factory=list)
    technologies: list[ProjectSummaryItemResponse] = Field(default_factory=list)
    decisions: list[str] = Field(default_factory=list)
    open_tasks: list[str] = Field(default_factory=list)
    recent_events: list[str] = Field(default_factory=list)
    source_coverage: list[ProjectSummaryItemResponse] = Field(default_factory=list)
    processing_health: ProcessingHealthResponse


class StatusReportBody(BaseModel):
    start_at: datetime | None = None
    end_at: datetime | None = None


class StatusReportResponse(BaseModel):
    title: str
    period_start: datetime | None
    period_end: datetime | None
    summary: str
    decisions: list[str]
    tasks: list[str]
    events: list[str]
    technologies: list[str]
    citations: list[str]
    generated_at: datetime


class ProjectReportBody(BaseModel):
    start_at: datetime | None = None
    end_at: datetime | None = None


class ProjectReportResponse(BaseModel):
    id: str
    project_entity_id: str
    status: str
    title: str
    markdown: str | None = None
    citations: list[str] = Field(default_factory=list)
    period_start: datetime | None = None
    period_end: datetime | None = None
    error_summary: str | None = None
    created_at: datetime
    completed_at: datetime | None = None
