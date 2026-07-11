from uuid import UUID

from domain.errors import DomainError
from domain.projects import StatusReportRequest
from fastapi import APIRouter, Depends
from starlette.responses import JSONResponse

from api.dependencies import RequestServices, domain_error_response, get_services
from api.schemas.projects import (
    ProcessingHealthResponse,
    ProjectDashboardResponse,
    ProjectReportBody,
    ProjectReportResponse,
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


def _to_report_response(report: object) -> ProjectReportResponse:
    from domain.report import ProjectReportArtifact

    assert isinstance(report, ProjectReportArtifact)
    return ProjectReportResponse(
        id=str(report.id),
        project_entity_id=str(report.project_entity_id),
        status=report.status.value,
        title=report.title,
        markdown=report.markdown,
        citations=report.citations,
        period_start=report.period_start,
        period_end=report.period_end,
        error_summary=report.error_summary,
        created_at=report.created_at,
        completed_at=report.completed_at,
    )


@router.post("/projects/{project_id}/reports", response_model=ProjectReportResponse)
async def create_project_report(
    project_id: UUID,
    body: ProjectReportBody,
    services: RequestServices = Depends(get_services),
) -> ProjectReportResponse | JSONResponse:
    try:
        job = await services.project_reports.enqueue(
            services.owner,
            project_id,
            start_at=body.start_at,
            end_at=body.end_at,
        )
        return _to_report_response(job)
    except DomainError as exc:
        return JSONResponse(
            status_code=404,
            content=domain_error_response(exc, services.correlation_id),
        )


@router.get(
    "/projects/{project_id}/reports/{report_id}",
    response_model=ProjectReportResponse,
)
async def get_project_report(
    project_id: UUID,
    report_id: UUID,
    services: RequestServices = Depends(get_services),
) -> ProjectReportResponse | JSONResponse:
    job = await services.project_reports.get_job(services.owner, project_id, report_id)
    if job is None:
        return JSONResponse(
            status_code=404,
            content=domain_error_response(DomainError("Report not found"), services.correlation_id),
        )
    return _to_report_response(job)
