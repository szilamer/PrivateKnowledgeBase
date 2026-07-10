from domain.identity import OwnerContext
from domain.projects import ProcessingHealth, ProjectDashboard, ProjectSummaryItem

from application.policy import LocalPolicyService
from application.ports import SourceRepository
from application.ports.canonical import CanonicalRepository, OutboxRepository


class ProjectDashboardService:
    """MVP-07 / FR-PRJ-001 — project intelligence dashboard."""

    def __init__(
        self,
        canonical: CanonicalRepository,
        sources: SourceRepository,
        outbox: OutboxRepository,
        policy: LocalPolicyService,
    ) -> None:
        self._canonical = canonical
        self._sources = sources
        self._outbox = outbox
        self._policy = policy

    async def get_dashboard(self, owner: OwnerContext) -> ProjectDashboard:
        self._policy.authorize_owner(owner, owner.owner_id)
        owner_id = owner.owner_id

        projects = await self._canonical.list_entities_by_type(owner_id, "project", limit=20)
        people = await self._canonical.list_entities_by_type(owner_id, "person", limit=20)
        repositories = await self._canonical.list_entities_by_type(owner_id, "repository", limit=20)
        technologies = await self._canonical.list_entities_by_type(owner_id, "technology", limit=20)
        decisions = await self._canonical.list_claims_by_predicate(
            owner_id, "has_decision", limit=20
        )
        tasks = await self._canonical.list_claims_by_predicate(owner_id, "has_task", limit=20)
        events = await self._canonical.list_claims_by_predicate(owner_id, "has_event", limit=20)

        source_items, _ = await self._sources.list_by_owner(owner_id, limit=50, cursor=None)
        enabled = sum(1 for source in source_items if source.enabled)

        health = ProcessingHealth(
            sources_total=len(source_items),
            sources_enabled=enabled,
            open_contradictions=await self._canonical.count_open_contradictions(owner_id),
            pending_outbox_events=await self._outbox.pending_count(),
        )

        return ProjectDashboard(
            summary=(
                f"{len(projects)} projects, {len(repositories)} repositories, "
                f"{len(tasks)} open tasks, {health.open_contradictions} contradictions"
            ),
            projects=[
                ProjectSummaryItem(id=item.id, name=item.canonical_name, entity_type="project")
                for item in projects
            ],
            people=[
                ProjectSummaryItem(id=item.id, name=item.canonical_name, entity_type="person")
                for item in people
            ],
            repositories=[
                ProjectSummaryItem(id=item.id, name=item.canonical_name, entity_type="repository")
                for item in repositories
            ],
            technologies=[
                ProjectSummaryItem(id=item.id, name=item.canonical_name, entity_type="technology")
                for item in technologies
            ],
            decisions=[claim.object_value for claim in decisions],
            open_tasks=[claim.object_value for claim in tasks],
            recent_events=[claim.object_value for claim in events],
            source_coverage=[
                ProjectSummaryItem(id=source.id, name=source.name, entity_type=source.type.value)
                for source in source_items
            ],
            processing_health=health,
        )
