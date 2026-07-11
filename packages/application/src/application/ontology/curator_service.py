from typing import cast
from uuid import UUID

from application.policy import LocalPolicyService
from application.ports.knowledge import AuditWriter
from application.ports.ontology import OntologyProposalRepository, UnmappedConceptReader
from domain.audit import AuditAction, AuditEvent
from domain.errors import DomainError
from domain.identity import OwnerContext
from domain.ontology_proposals import (
    MIN_UNMAPPED_OCCURRENCES,
    OntologyProposal,
    OntologyProposalStatus,
    UnmappedEntityCandidate,
    UnmappedRelationshipCandidate,
)


class OntologyCuratorService:
    """Phase E — detect unmapped concepts and create governed ontology proposals."""

    def __init__(
        self,
        proposals: OntologyProposalRepository,
        unmapped: UnmappedConceptReader,
        policy: LocalPolicyService,
        audit: AuditWriter | None = None,
    ) -> None:
        self._proposals = proposals
        self._unmapped = unmapped
        self._policy = policy
        self._audit = audit

    async def scan_and_propose(self, owner: OwnerContext) -> list[OntologyProposal]:
        self._policy.authorize_owner(owner, owner.owner_id)
        final = await self._run_graph(owner.owner_id)
        created = final.get("proposals", [])
        if not isinstance(created, list):
            return []
        proposals = [item for item in created if isinstance(item, OntologyProposal)]
        if self._audit is not None and proposals:
            from datetime import UTC, datetime
            from uuid import uuid4

            await self._audit.append(
                AuditEvent(
                    id=uuid4(),
                    actor_id=owner.owner_id,
                    action=AuditAction.ONTOLOGY_PROPOSAL_CREATED,
                    object_type="ontology_scan",
                    object_id=owner.owner_id,
                    correlation_id=str(owner.owner_id),
                    metadata={"created_count": len(proposals)},
                    created_at=datetime.now(UTC),
                )
            )
        return proposals

    async def list_proposals(
        self,
        owner: OwnerContext,
        *,
        status: OntologyProposalStatus | None = OntologyProposalStatus.PENDING,
        limit: int = 50,
    ) -> list[OntologyProposal]:
        self._policy.authorize_owner(owner, owner.owner_id)
        return await self._proposals.list_proposals(
            owner.owner_id,
            status=status,
            limit=limit,
        )

    async def get_proposal(self, owner: OwnerContext, proposal_id: UUID) -> OntologyProposal:
        self._policy.authorize_owner(owner, owner.owner_id)
        proposal = await self._proposals.get_by_id(proposal_id, owner.owner_id)
        if proposal is None:
            raise DomainError("Ontology proposal not found")
        return proposal

    async def approve(
        self,
        owner: OwnerContext,
        proposal_id: UUID,
        *,
        rationale: str | None = None,
    ) -> OntologyProposal:
        return await self._decide(
            owner,
            proposal_id,
            status=OntologyProposalStatus.APPROVED,
            rationale=rationale,
        )

    async def reject(
        self,
        owner: OwnerContext,
        proposal_id: UUID,
        *,
        rationale: str | None = None,
    ) -> OntologyProposal:
        return await self._decide(
            owner,
            proposal_id,
            status=OntologyProposalStatus.REJECTED,
            rationale=rationale,
        )

    async def _decide(
        self,
        owner: OwnerContext,
        proposal_id: UUID,
        *,
        status: OntologyProposalStatus,
        rationale: str | None,
    ) -> OntologyProposal:
        self._policy.authorize_owner(owner, owner.owner_id)
        proposal = await self.get_proposal(owner, proposal_id)
        if proposal.status != OntologyProposalStatus.PENDING:
            raise DomainError("Only pending ontology proposals can be decided")
        updated = await self._proposals.update_status(
            proposal_id,
            owner.owner_id,
            status=status,
            decision_rationale=rationale,
        )
        if updated is None:
            raise DomainError("Ontology proposal not found")
        return updated

    async def _run_graph(self, owner_id: UUID) -> dict[str, object]:
        from agents.ontology.graph import build_ontology_curator_graph

        async def load_entities(requested_owner: UUID) -> list[UnmappedEntityCandidate]:
            return await self._unmapped.aggregate_unmapped_entities(
                requested_owner,
                min_occurrences=MIN_UNMAPPED_OCCURRENCES,
            )

        async def load_relationships(
            requested_owner: UUID,
        ) -> list[UnmappedRelationshipCandidate]:
            return await self._unmapped.aggregate_unmapped_relationships(
                requested_owner,
                min_occurrences=MIN_UNMAPPED_OCCURRENCES,
            )

        async def persist(
            requested_owner: UUID,
            items: list[OntologyProposal],
        ) -> list[OntologyProposal]:
            _ = requested_owner
            return await self._proposals.create_proposals(items)

        graph = build_ontology_curator_graph(
            load_unmapped_entities=load_entities,
            load_unmapped_relationships=load_relationships,
            persist_proposals=persist,
        )
        return cast(
            dict[str, object],
            await graph.ainvoke({"owner_id": owner_id}),
        )
