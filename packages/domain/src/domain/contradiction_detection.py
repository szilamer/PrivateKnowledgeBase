from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

from domain.canonical import CanonicalClaim, ContradictionFinding, ContradictionStatus
from domain.proposals import KnowledgeProposal


@dataclass(frozen=True)
class ContradictionEvidence:
    predicate: str
    existing_value: str
    conflicting_value: str
    subject_entity_id: UUID | None
    existing_claim_id: UUID
    conflicting_claim_id: UUID | None = None
    conflicting_proposal_id: UUID | None = None

    def as_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "predicate": self.predicate,
            "existing_value": self.existing_value,
            "conflicting_value": self.conflicting_value,
            "existing_claim_id": str(self.existing_claim_id),
        }
        if self.subject_entity_id is not None:
            payload["subject_entity_id"] = str(self.subject_entity_id)
        if self.conflicting_claim_id is not None:
            payload["conflicting_claim_id"] = str(self.conflicting_claim_id)
        if self.conflicting_proposal_id is not None:
            payload["conflicting_proposal_id"] = str(self.conflicting_proposal_id)
        return payload


def values_contradict(existing_value: str, new_value: str) -> bool:
    return existing_value.strip().lower() != new_value.strip().lower()


def compare_claim_against_candidates(
    *,
    owner_id: UUID,
    new_claim: CanonicalClaim,
    candidates: list[CanonicalClaim],
    proposal: KnowledgeProposal,
    now: datetime,
) -> list[ContradictionFinding]:
    """Deterministic contradiction comparison — informational only (Phase D, D-4)."""
    findings: list[ContradictionFinding] = []
    for prior in candidates:
        if prior.id == new_claim.id:
            continue
        if not values_contradict(prior.object_value, new_claim.object_value):
            continue
        evidence = ContradictionEvidence(
            predicate=new_claim.predicate,
            existing_value=prior.object_value,
            conflicting_value=new_claim.object_value,
            subject_entity_id=new_claim.subject_entity_id,
            existing_claim_id=prior.id,
            conflicting_claim_id=new_claim.id,
            conflicting_proposal_id=proposal.id,
        )
        findings.append(
            ContradictionFinding(
                id=uuid4(),
                owner_id=owner_id,
                existing_claim_id=prior.id,
                conflicting_claim_id=new_claim.id,
                conflicting_proposal_id=proposal.id,
                status=ContradictionStatus.OPEN,
                summary=(
                    f"Potential contradiction on '{new_claim.predicate}': "
                    f"'{prior.object_value}' vs '{new_claim.object_value}'"
                ),
                evidence=evidence.as_dict(),
                created_at=now,
                updated_at=now,
            )
        )
    return findings
