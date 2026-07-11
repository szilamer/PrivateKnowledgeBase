from domain.entities import EntityType
from domain.entity_resolution import classify_risk, requires_review
from domain.proposals import ProposalStatus, ProposalType, RiskLevel


def test_classify_risk_low_for_high_confidence_technology() -> None:
    assert classify_risk(EntityType.TECHNOLOGY, 0.9) == RiskLevel.LOW.value


def test_classify_risk_high_for_low_confidence() -> None:
    assert classify_risk(EntityType.PERSON, 0.5) == RiskLevel.HIGH.value


def test_requires_review_entity_resolution() -> None:
    assert requires_review("low", ProposalType.ENTITY_RESOLUTION.value) is True


def test_requires_review_merge() -> None:
    assert requires_review("low", ProposalType.MERGE.value) is True


def test_requires_review_auto_approves_high_confidence_entity() -> None:
    assert requires_review("medium", ProposalType.ENTITY.value, confidence=0.82) is False


def test_requires_review_keeps_low_confidence_entity() -> None:
    assert requires_review("medium", ProposalType.ENTITY.value, confidence=0.75) is True


def test_requires_review_keeps_relationships() -> None:
    assert requires_review("low", ProposalType.RELATIONSHIP.value, confidence=0.9) is True


def test_pending_is_default_proposal_status() -> None:
    assert ProposalStatus.PENDING.value == "pending"
