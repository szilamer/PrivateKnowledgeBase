from datetime import UTC, datetime
from uuid import UUID, uuid4

from domain.approval import ApprovalAction, ApprovalDecision
from domain.audit import AuditAction, AuditEvent
from domain.errors import DomainError
from domain.identity import OwnerContext
from domain.proposals import (
    KnowledgeProposal,
    ProposalFilter,
    ProposalStatus,
    ProposalType,
    RiskLevel,
)

from application.policy import LocalPolicyService
from application.ports.canonical import CanonicalMaterializer, ProjectionDispatcher
from application.ports.knowledge import (
    ApprovalRepository,
    AuditWriter,
    ProposalRepository,
)


class ProposalService:
    """Phase 3 — approval queue and decisions (MVP-04, FR-APR-001..004)."""

    BATCH_APPROVABLE_TYPES = {ProposalType.ENTITY}

    def __init__(
        self,
        proposals: ProposalRepository,
        approvals: ApprovalRepository,
        materializer: CanonicalMaterializer,
        audit: AuditWriter,
        policy: LocalPolicyService,
        on_materialized: ProjectionDispatcher | None = None,
    ) -> None:
        self._proposals = proposals
        self._approvals = approvals
        self._materializer = materializer
        self._audit = audit
        self._policy = policy
        self._on_materialized = on_materialized

    async def list_proposals(
        self, owner: OwnerContext, filters: ProposalFilter
    ) -> tuple[list[KnowledgeProposal], UUID | None]:
        self._policy.authorize_owner(owner, owner.owner_id)
        return await self._proposals.list_proposals(owner.owner_id, filters)

    async def get_proposal(self, owner: OwnerContext, proposal_id: UUID) -> KnowledgeProposal:
        self._policy.authorize_owner(owner, owner.owner_id)
        proposal = await self._proposals.get_by_id(proposal_id, owner.owner_id)
        if proposal is None:
            raise DomainError("Proposal not found")
        return proposal

    async def approve(
        self,
        owner: OwnerContext,
        proposal_id: UUID,
        *,
        rationale: str | None = None,
        correlation_id: str,
    ) -> KnowledgeProposal:
        return await self._decide(
            owner,
            proposal_id,
            action=ApprovalAction.APPROVE,
            rationale=rationale,
            correlation_id=correlation_id,
        )

    async def reject(
        self,
        owner: OwnerContext,
        proposal_id: UUID,
        *,
        rationale: str | None = None,
        correlation_id: str,
    ) -> KnowledgeProposal:
        return await self._decide(
            owner,
            proposal_id,
            action=ApprovalAction.REJECT,
            rationale=rationale,
            correlation_id=correlation_id,
        )

    async def defer(
        self,
        owner: OwnerContext,
        proposal_id: UUID,
        *,
        rationale: str | None = None,
        correlation_id: str,
    ) -> KnowledgeProposal:
        return await self._decide(
            owner,
            proposal_id,
            action=ApprovalAction.DEFER,
            rationale=rationale,
            correlation_id=correlation_id,
        )

    async def edit_and_approve(
        self,
        owner: OwnerContext,
        proposal_id: UUID,
        *,
        edited_payload: dict[str, object],
        rationale: str | None = None,
        correlation_id: str,
    ) -> KnowledgeProposal:
        proposal = await self.get_proposal(owner, proposal_id)
        if proposal.status != ProposalStatus.PENDING:
            raise DomainError("Only pending proposals can be edited")

        updated = await self._proposals.update_status(
            proposal_id,
            owner.owner_id,
            ProposalStatus.APPROVED.value,
            payload=edited_payload,
            original_payload=proposal.payload,
        )
        if updated is None:
            raise DomainError("Proposal not found")

        await self._record_decision(
            owner,
            proposal_id,
            ApprovalAction.EDIT_AND_APPROVE,
            rationale=rationale,
            edited_payload=edited_payload,
            correlation_id=correlation_id,
        )
        await self._on_approved(owner, updated)
        return updated

    async def batch_approve(
        self,
        owner: OwnerContext,
        proposal_ids: list[UUID],
        *,
        correlation_id: str,
    ) -> list[KnowledgeProposal]:
        approved: list[KnowledgeProposal] = []
        for proposal_id in proposal_ids:
            proposal = await self.get_proposal(owner, proposal_id)
            if proposal.status != ProposalStatus.PENDING:
                raise DomainError(f"Proposal {proposal_id} is not pending")
            if proposal.risk_level != RiskLevel.LOW:
                raise DomainError("Batch approval only allowed for low-risk proposals")
            if proposal.requires_review:
                raise DomainError("Proposal requires individual review")
            approved.append(await self.approve(owner, proposal_id, correlation_id=correlation_id))
        return approved

    async def _decide(
        self,
        owner: OwnerContext,
        proposal_id: UUID,
        *,
        action: ApprovalAction,
        rationale: str | None,
        correlation_id: str,
    ) -> KnowledgeProposal:
        proposal = await self.get_proposal(owner, proposal_id)
        if proposal.status != ProposalStatus.PENDING:
            raise DomainError("Proposal is not pending")

        status_map = {
            ApprovalAction.APPROVE: ProposalStatus.APPROVED,
            ApprovalAction.REJECT: ProposalStatus.REJECTED,
            ApprovalAction.DEFER: ProposalStatus.DEFERRED,
        }
        new_status = status_map.get(action)
        if new_status is None:
            raise DomainError("Unsupported action")

        updated = await self._proposals.update_status(proposal_id, owner.owner_id, new_status.value)
        if updated is None:
            raise DomainError("Proposal not found")

        await self._record_decision(
            owner, proposal_id, action, rationale=rationale, correlation_id=correlation_id
        )
        if action == ApprovalAction.APPROVE:
            await self._on_approved(owner, updated)
        return updated

    async def _on_approved(self, owner: OwnerContext, proposal: KnowledgeProposal) -> None:
        await self._materializer.materialize_approved_proposal(owner.owner_id, proposal)
        if self._on_materialized is not None:
            await self._on_materialized.enqueue_projection()

    async def _record_decision(
        self,
        owner: OwnerContext,
        proposal_id: UUID,
        action: ApprovalAction,
        *,
        rationale: str | None,
        correlation_id: str,
        edited_payload: dict[str, object] | None = None,
    ) -> None:
        decision = ApprovalDecision(
            id=uuid4(),
            proposal_id=proposal_id,
            actor_id=owner.owner_id,
            action=action,
            rationale=rationale,
            edited_payload=edited_payload,
            correlation_id=correlation_id,
            created_at=datetime.now(UTC),
        )
        await self._approvals.record_decision(decision)

        audit_action = {
            ApprovalAction.APPROVE: AuditAction.PROPOSAL_APPROVED,
            ApprovalAction.REJECT: AuditAction.PROPOSAL_REJECTED,
            ApprovalAction.DEFER: AuditAction.PROPOSAL_DEFERRED,
            ApprovalAction.EDIT_AND_APPROVE: AuditAction.PROPOSAL_EDITED,
        }.get(action)
        if audit_action and hasattr(self._audit, "append"):
            event = AuditEvent(
                id=uuid4(),
                actor_id=owner.owner_id,
                action=audit_action,
                object_type="knowledge_proposal",
                object_id=proposal_id,
                correlation_id=correlation_id,
                metadata={"action": action.value},
                created_at=datetime.now(UTC),
            )
            await self._audit.append(event)
