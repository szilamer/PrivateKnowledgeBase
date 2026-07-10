from domain.projects import StatusReportRequest
from fastapi import APIRouter, Depends

from api.dependencies import RequestServices, get_services
from api.schemas.projects import (
    ProcessingHealthResponse,
    ProjectDashboardResponse,
    ProjectSummaryItemResponse,
    StatusReportBody,
    StatusReportResponse,
)

router = APIRouter(tags=["projects"])


@router.get("/projects/overview", response_model=ProjectDashboardResponse)
async def project_overview(
    services: RequestServices = Depends(get_services),
) -> ProjectDashboardResponse:
    dashboard = await services.dashboard.get_dashboard(services.owner)
    health = dashboard.processing_health
    return ProjectDashboardResponse(
        summary=dashboard.summary,
        projects=[
            ProjectSummaryItemResponse(
                id=str(item.id), name=item.name, entity_type=item.entity_type
            )
            for item in dashboard.projects
        ],
        people=[
            ProjectSummaryItemResponse(
                id=str(item.id), name=item.name, entity_type=item.entity_type
            )
            for item in dashboard.people
        ],
        repositories=[
            ProjectSummaryItemResponse(
                id=str(item.id), name=item.name, entity_type=item.entity_type
            )
            for item in dashboard.repositories
        ],
        technologies=[
            ProjectSummaryItemResponse(
                id=str(item.id), name=item.name, entity_type=item.entity_type
            )
            for item in dashboard.technologies
        ],
        decisions=dashboard.decisions,
        open_tasks=dashboard.open_tasks,
        recent_events=dashboard.recent_events,
        source_coverage=[
            ProjectSummaryItemResponse(
                id=str(item.id), name=item.name, entity_type=item.entity_type
            )
            for item in dashboard.source_coverage
        ],
        processing_health=ProcessingHealthResponse(
            sources_total=health.sources_total,
            sources_enabled=health.sources_enabled,
            pending_proposals=health.pending_proposals,
            open_contradictions=health.open_contradictions,
            pending_outbox_events=health.pending_outbox_events,
            last_sync_at=health.last_sync_at,
        ),
    )


@router.post("/projects/status-report", response_model=StatusReportResponse)
async def status_report(
    body: StatusReportBody,
    services: RequestServices = Depends(get_services),
) -> StatusReportResponse:
    report = await services.reports.generate(
        services.owner,
        StatusReportRequest(start_at=body.start_at, end_at=body.end_at),
    )
    return StatusReportResponse(
        title=report.title,
        period_start=report.period_start,
        period_end=report.period_end,
        summary=report.summary,
        decisions=report.decisions,
        tasks=report.tasks,
        events=report.events,
        technologies=report.technologies,
        citations=report.citations,
        generated_at=report.generated_at,
    )
