from datetime import UTC, datetime

from domain.identity import OwnerContext
from domain.projects import StatusReport, StatusReportRequest

from application.policy import LocalPolicyService
from application.ports.canonical import CanonicalRepository


class StatusReportService:
    """FR-PRJ-002 — time-bounded source-backed status report."""

    def __init__(self, canonical: CanonicalRepository, policy: LocalPolicyService) -> None:
        self._canonical = canonical
        self._policy = policy

    async def generate(self, owner: OwnerContext, request: StatusReportRequest) -> StatusReport:
        self._policy.authorize_owner(owner, owner.owner_id)
        owner_id = owner.owner_id
        now = datetime.now(UTC)

        decisions = await self._canonical.list_claims_by_predicate(
            owner_id,
            "has_decision",
            limit=50,
            since=request.start_at,
            until=request.end_at,
        )
        tasks = await self._canonical.list_claims_by_predicate(
            owner_id,
            "has_task",
            limit=50,
            since=request.start_at,
            until=request.end_at,
        )
        events = await self._canonical.list_claims_by_predicate(
            owner_id,
            "has_event",
            limit=50,
            since=request.start_at,
            until=request.end_at,
        )
        technologies = await self._canonical.list_entities_by_type(owner_id, "technology", limit=30)

        citations: list[str] = []
        for claim in decisions + tasks + events:
            for prov in claim.provenance:
                if prov.proposal_id:
                    citations.append(f"proposal:{prov.proposal_id}")
                if prov.content_chunk_id:
                    citations.append(f"chunk:{prov.content_chunk_id}")

        period = ""
        if request.start_at:
            period += f" from {request.start_at.date()}"
        if request.end_at:
            period += f" to {request.end_at.date()}"

        return StatusReport(
            title=f"Project status report{period}",
            period_start=request.start_at,
            period_end=request.end_at,
            summary=(
                f"{len(decisions)} decisions, {len(tasks)} tasks, "
                f"{len(events)} events in the selected period."
            ),
            decisions=[claim.object_value for claim in decisions],
            tasks=[claim.object_value for claim in tasks],
            events=[claim.object_value for claim in events],
            technologies=[entity.canonical_name for entity in technologies],
            citations=sorted(set(citations)),
            generated_at=now,
        )
