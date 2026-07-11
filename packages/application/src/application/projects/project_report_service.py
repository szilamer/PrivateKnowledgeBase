from datetime import datetime
from typing import Protocol, cast
from uuid import UUID, uuid4

from domain.errors import DomainError
from domain.identity import OwnerContext
from domain.report import (
    PROJECT_REPORT_PIPELINE_VERSION,
    ProjectReportArtifact,
    ProjectReportRequest,
    ProjectSubgraphData,
)

from application.policy import LocalPolicyService
from application.ports.canonical import CanonicalRepository
from application.ports.report import ProjectReportRepository


class ReportJobDispatcher(Protocol):
    async def enqueue_project_report(self, report_id: UUID, owner_id: UUID) -> None: ...


class ProjectReportService:
    """Phase H — LangGraph project reports with async Celery generation."""

    def __init__(
        self,
        canonical: CanonicalRepository,
        reports: ProjectReportRepository,
        policy: LocalPolicyService,
        dispatcher: ReportJobDispatcher | None = None,
    ) -> None:
        self._canonical = canonical
        self._reports = reports
        self._policy = policy
        self._dispatcher = dispatcher

    async def enqueue(
        self,
        owner: OwnerContext,
        project_entity_id: UUID,
        *,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
    ) -> ProjectReportArtifact:
        self._policy.authorize_owner(owner, owner.owner_id)
        entity = await self._canonical.get_entity(project_entity_id, owner.owner_id)
        if entity is None:
            msg = "Project not found"
            raise DomainError(msg)

        request = ProjectReportRequest(
            project_entity_id=project_entity_id,
            start_at=start_at,
            end_at=end_at,
        )
        job_id = uuid4()
        title = f"Projektjelentés: {entity.canonical_name}"
        job = await self._reports.create_job(
            job_id=job_id,
            owner_id=owner.owner_id,
            request=request,
            title=title,
        )
        if self._dispatcher is not None:
            await self._dispatcher.enqueue_project_report(job_id, owner.owner_id)
        return job

    async def get_job(
        self,
        owner: OwnerContext,
        project_entity_id: UUID,
        report_id: UUID,
    ) -> ProjectReportArtifact | None:
        self._policy.authorize_owner(owner, owner.owner_id)
        job = await self._reports.get_job(report_id, owner.owner_id)
        if job is None or job.project_entity_id != project_entity_id:
            return None
        return job

    async def generate(self, report_id: UUID, owner_id: UUID) -> None:
        job = await self._reports.get_job(report_id, owner_id)
        if job is None:
            msg = f"Report job not found: {report_id}"
            raise ValueError(msg)

        await self._reports.mark_running(report_id)
        try:
            final = await self._run_graph(
                owner_id=owner_id,
                project_entity_id=job.project_entity_id,
                start_at=job.period_start,
                end_at=job.period_end,
            )
            subgraph_raw = final.get("subgraph")
            if not isinstance(subgraph_raw, ProjectSubgraphData):
                msg = "Report graph did not return subgraph"
                raise TypeError(msg)
            subgraph = subgraph_raw
            await self._reports.complete_job(
                report_id,
                title=str(final.get("title") or job.title),
                markdown=str(final.get("markdown") or ""),
                citations=subgraph.citations,
                provenance={
                    "pipeline_version": final.get(
                        "pipeline_version", PROJECT_REPORT_PIPELINE_VERSION
                    ),
                    "project_entity_id": str(job.project_entity_id),
                    "decision_count": len(subgraph.decisions),
                    "task_count": len(subgraph.tasks),
                },
            )
        except Exception as exc:  # noqa: BLE001
            await self._reports.fail_job(report_id, error_summary=str(exc))
            raise

    async def _run_graph(
        self,
        *,
        owner_id: UUID,
        project_entity_id: UUID,
        start_at: datetime | None,
        end_at: datetime | None,
    ) -> dict[str, object]:
        from agents.report.graph import build_report_graph

        graph = build_report_graph(load_subgraph=self._load_subgraph)
        final = cast(
            dict[str, object],
            await graph.ainvoke(
                {
                    "owner_id": owner_id,
                    "project_entity_id": project_entity_id,
                    "start_at": start_at,
                    "end_at": end_at,
                }
            ),
        )
        return final

    async def _load_subgraph(
        self,
        owner_id: UUID,
        project_entity_id: UUID,
        start_at: datetime | None,
        end_at: datetime | None,
    ) -> ProjectSubgraphData:
        entity = await self._canonical.get_entity(project_entity_id, owner_id)
        if entity is None:
            msg = "Project not found"
            raise DomainError(msg)

        decisions = await self._canonical.list_claims_by_predicate(
            owner_id,
            "has_decision",
            limit=50,
            since=start_at,
            until=end_at,
        )
        tasks = await self._canonical.list_claims_by_predicate(
            owner_id,
            "has_task",
            limit=50,
            since=start_at,
            until=end_at,
        )
        events = await self._canonical.list_claims_by_predicate(
            owner_id,
            "has_event",
            limit=50,
            since=start_at,
            until=end_at,
        )
        technologies = await self._canonical.list_entities_by_type(
            owner_id,
            "technology",
            limit=30,
        )
        contradictions = await self._canonical.list_contradictions(
            owner_id,
            status="open",
            limit=20,
        )

        scoped_decisions = [
            claim.object_value
            for claim in decisions
            if claim.subject_entity_id in {None, project_entity_id}
        ]
        scoped_tasks = [
            claim.object_value
            for claim in tasks
            if claim.subject_entity_id in {None, project_entity_id}
        ]
        scoped_events = [
            claim.object_value
            for claim in events
            if claim.subject_entity_id in {None, project_entity_id}
        ]

        citations: list[str] = []
        for claim in decisions + tasks + events:
            for prov in claim.provenance:
                if prov.proposal_id:
                    citations.append(f"proposal:{prov.proposal_id}")
                if prov.content_chunk_id:
                    citations.append(f"chunk:{prov.content_chunk_id}")

        risks = [finding.summary for finding in contradictions]

        return ProjectSubgraphData(
            project_name=entity.canonical_name,
            decisions=scoped_decisions,
            tasks=scoped_tasks,
            events=scoped_events,
            risks=risks,
            technologies=[item.canonical_name for item in technologies],
            citations=sorted(set(citations)),
        )
