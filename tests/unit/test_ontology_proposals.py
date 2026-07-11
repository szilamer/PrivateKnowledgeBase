from domain.ontology_proposals import (
    OntologyProposalKind,
    OntologyProposalStatus,
    UnmappedEntityCandidate,
)


def test_unmapped_entity_candidate_defaults() -> None:
    candidate = UnmappedEntityCandidate(
        name="Next.js",
        entity_type="technology",
        occurrence_count=4,
    )
    assert candidate.sample_proposal_ids == []
    assert candidate.occurrence_count == 4


def test_ontology_proposal_status_values() -> None:
    assert OntologyProposalStatus.PENDING.value == "pending"
    assert OntologyProposalKind.ENTITY_TYPE.value == "entity_type"
