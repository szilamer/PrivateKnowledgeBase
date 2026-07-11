from uuid import UUID

from adapters.persistence.canonical_repository import PostgresCanonicalRepository
from adapters.persistence.report_repository import PostgresProjectReportRepository
from application.policy import LocalPolicyService
from application.projects.project_report_service import ProjectReportService
from celery import Task
from observability.logging import get_logger

from worker.celery_app import celery_app
from worker.db import run_task, task_session

logger = get_logger("worker.tasks.reports")


async def _generate_project_report(report_id: UUID, owner_id: UUID) -> dict[str, str]:
    async with task_session() as session:
        service = ProjectReportService(
            canonical=PostgresCanonicalRepository(session),
            reports=PostgresProjectReportRepository(session),
            policy=LocalPolicyService(),
        )
        await service.generate(report_id, owner_id)
    logger.info("project_report_complete", report_id=str(report_id))
    return {"report_id": str(report_id), "status": "completed"}


@celery_app.task(name="worker.tasks.reports.generate_project_report", bind=True)
def generate_project_report(
    self: Task,
    report_id: str,
    owner_id: str,
    **kwargs: object,
) -> dict[str, str]:
    logger.info(
        "project_report_started",
        report_id=report_id,
        owner_id=owner_id,
        task_id=self.request.id,
    )
    return run_task(
        lambda: _generate_project_report(UUID(report_id), UUID(owner_id)),
    )
