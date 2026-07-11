from datetime import UTC, datetime
from uuid import uuid4

import pytest
from domain.canonical import CanonicalClaim, ClaimStatus
from domain.contradiction_detection import (
    compare_claim_against_candidates,
    values_contradict,
)
from domain.proposals import KnowledgeProposal, ProposalStatus, ProposalType, RiskLevel


def test_values_contradict_detects_mismatch() -> None:
    assert values_contradict("Use MySQL", "Use PostgreSQL") is True


def test_values_contradict_ignores_case_and_whitespace() -> None:
    assert values_contradict(" PostgreSQL ", "postgresql") is False


def test_compare_claim_against_candidates_creates_finding_with_evidence() -> None:
    owner_id = uuid4()
    now = datetime.now(UTC)
    existing = CanonicalClaim(
        id=uuid4(),
        owner_id=owner_id,
        subject_entity_id=uuid4(),
        predicate="uses_technology",
        object_value="MySQL",
        confidence=0.9,
        created_at=now,
        updated_at=now,
    )
    new_claim = CanonicalClaim(
        id=uuid4(),
        owner_id=owner_id,
        subject_entity_id=existing.subject_entity_id,
        predicate="uses_technology",
        object_value="PostgreSQL",
        confidence=0.88,
        created_at=now,
        updated_at=now,
    )
    proposal = KnowledgeProposal(
        id=uuid4(),
        owner_id=owner_id,
        extraction_run_id=None,
        proposal_type=ProposalType.CLAIM,
        status=ProposalStatus.APPROVED,
        risk_level=RiskLevel.LOW,
        confidence=0.88,
        title="Database choice",
        payload={"predicate": "uses_technology", "value": "PostgreSQL"},
        requires_review=False,
        created_at=now,
        updated_at=now,
    )

    findings = compare_claim_against_candidates(
        owner_id=owner_id,
        new_claim=new_claim,
        candidates=[existing],
        proposal=proposal,
        now=now,
    )

    assert len(findings) == 1
    finding = findings[0]
    assert finding.existing_claim_id == existing.id
    assert finding.conflicting_claim_id == new_claim.id
    assert finding.conflicting_proposal_id == proposal.id
    assert finding.evidence["predicate"] == "uses_technology"
    assert finding.evidence["existing_value"] == "MySQL"
    assert finding.evidence["conflicting_value"] == "PostgreSQL"


@pytest.mark.asyncio
async def test_contradiction_graph_detects_conflict() -> None:
    from agents.contradiction.graph import build_contradiction_graph
    from domain.proposals import KnowledgeProposal, ProposalStatus, ProposalType, RiskLevel

    owner_id = uuid4()
    now = datetime.now(UTC)
    subject_id = uuid4()
    existing = CanonicalClaim(
        id=uuid4(),
        owner_id=owner_id,
        subject_entity_id=subject_id,
        predicate="uses_technology",
        object_value="MySQL",
        status=ClaimStatus.ACTIVE,
        confidence=0.9,
        created_at=now,
        updated_at=now,
    )
    new_claim = CanonicalClaim(
        id=uuid4(),
        owner_id=owner_id,
        subject_entity_id=subject_id,
        predicate="uses_technology",
        object_value="PostgreSQL",
        status=ClaimStatus.ACTIVE,
        confidence=0.88,
        created_at=now,
        updated_at=now,
    )
    proposal = KnowledgeProposal(
        id=uuid4(),
        owner_id=owner_id,
        extraction_run_id=None,
        proposal_type=ProposalType.CLAIM,
        status=ProposalStatus.APPROVED,
        risk_level=RiskLevel.LOW,
        confidence=0.88,
        title="Database choice",
        payload={"predicate": "uses_technology", "value": "PostgreSQL"},
        requires_review=False,
        created_at=now,
        updated_at=now,
    )

    async def load_candidate_claims(
        requested_owner: object,
        subject_entity_id: object,
        predicate: str,
    ) -> list[CanonicalClaim]:
        assert requested_owner == owner_id
        assert subject_entity_id == subject_id
        assert predicate == "uses_technology"
        return [existing]

    graph = build_contradiction_graph(load_candidate_claims=load_candidate_claims, now=now)
    final = await graph.ainvoke({"owner_id": owner_id, "claim": new_claim, "proposal": proposal})

    findings = final.get("findings", [])
    assert len(findings) == 1
    assert final.get("candidate_count") == 1
