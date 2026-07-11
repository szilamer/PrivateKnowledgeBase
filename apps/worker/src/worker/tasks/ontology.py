from uuid import UUID

from adapters.persistence.ontology_repository import (
    PostgresOntologyProposalRepository,
    PostgresUnmappedConceptReader,
)
from adapters.persistence.repositories import PostgresAuditRepository
from application.ontology.curator_service import OntologyCuratorService
from application.policy import LocalPolicyService
from celery import Task
from domain.identity import DEFAULT_OWNER_ID, OwnerContext
from observability.logging import get_logger

from worker.celery_app import celery_app
from worker.db import run_task, task_session

logger = get_logger("worker.tasks.ontology")


async def _scan_unmapped(owner_id: UUID) -> dict[str, int]:
    async with task_session() as session:
        service = OntologyCuratorService(
            proposals=PostgresOntologyProposalRepository(session),
            unmapped=PostgresUnmappedConceptReader(session),
            policy=LocalPolicyService(),
            audit=PostgresAuditRepository(session),
        )
        created = await service.scan_and_propose(OwnerContext(owner_id=owner_id))
    logger.info("ontology_scan_complete", owner_id=str(owner_id), created=len(created))
    return {"created": len(created)}


@celery_app.task(name="worker.tasks.ontology.scan_unmapped", bind=True)
def scan_unmapped(self: Task, owner_id: str | None = None, **kwargs: object) -> dict[str, int]:
    resolved_owner = UUID(owner_id) if owner_id else DEFAULT_OWNER_ID
    logger.info(
        "ontology_scan_started",
        task_id=self.request.id,
        owner_id=str(resolved_owner),
    )
    return run_task(lambda: _scan_unmapped(resolved_owner))
