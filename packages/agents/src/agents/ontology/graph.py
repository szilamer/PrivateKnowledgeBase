from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from domain.ontology_proposals import (
    MIN_UNMAPPED_OCCURRENCES,
    ONTOLOGY_CURATOR_PIPELINE_VERSION,
    OntologyProposal,
    OntologyProposalKind,
    OntologyProposalStatus,
    UnmappedEntityCandidate,
    UnmappedRelationshipCandidate,
)
from langgraph.graph import END, StateGraph
from ontology.loader import OntologySnapshot, load_ontology_snapshot

from agents.ontology.state import OntologyCuratorState


def _title_for_entity(candidate: UnmappedEntityCandidate) -> str:
    return f"Új entitástípus: {candidate.entity_type}"


def _title_for_relationship(candidate: UnmappedRelationshipCandidate) -> str:
    return f"Új kapcsolattípus: {candidate.relationship_type}"


def build_ontology_curator_graph(
    *,
    load_unmapped_entities: Callable[[UUID], Awaitable[list[UnmappedEntityCandidate]]],
    load_unmapped_relationships: Callable[[UUID], Awaitable[list[UnmappedRelationshipCandidate]]],
    persist_proposals: Callable[[UUID, list[OntologyProposal]], Awaitable[list[OntologyProposal]]],
) -> Any:
    """LangGraph ontology curator — aggregate → read YAML → propose → persist."""

    async def aggregate_unmapped_node(state: OntologyCuratorState) -> OntologyCuratorState:
        owner_id = state["owner_id"]
        entities = await load_unmapped_entities(owner_id)
        relationships = await load_unmapped_relationships(owner_id)
        return {
            **state,
            "unmapped_entities": entities,
            "unmapped_relationships": relationships,
            "pipeline_version": ONTOLOGY_CURATOR_PIPELINE_VERSION,
        }

    async def read_ontology_node(state: OntologyCuratorState) -> OntologyCuratorState:
        snapshot = load_ontology_snapshot()
        return {**state, "ontology": snapshot}

    async def propose_additions_node(state: OntologyCuratorState) -> OntologyCuratorState:
        ontology = state.get("ontology") or OntologySnapshot()
        now = datetime.now(UTC)
        owner_id = state["owner_id"]
        proposals: list[OntologyProposal] = []

        known_entity_types = set(ontology.entity_type_ids)
        grouped_entities: dict[str, UnmappedEntityCandidate] = {}
        for candidate in state.get("unmapped_entities", []):
            current = grouped_entities.get(candidate.entity_type)
            if current is None or candidate.occurrence_count > current.occurrence_count:
                grouped_entities[candidate.entity_type] = candidate

        for candidate in grouped_entities.values():
            if candidate.entity_type in known_entity_types:
                continue
            if candidate.occurrence_count < MIN_UNMAPPED_OCCURRENCES:
                continue
            proposals.append(
                OntologyProposal(
                    id=uuid4(),
                    owner_id=owner_id,
                    kind=OntologyProposalKind.ENTITY_TYPE,
                    status=OntologyProposalStatus.PENDING,
                    title=_title_for_entity(candidate),
                    rationale=(
                        f"A(z) „{candidate.name}” entitás {candidate.occurrence_count} "
                        f"alkalommal jelent meg „{candidate.entity_type}” típusként, "
                        "de nincs a normatív ontológiában."
                    ),
                    proposed_definition={
                        "id": candidate.entity_type,
                        "label": candidate.entity_type.replace("_", " ").title(),
                        "description": f"Recurring extracted type for {candidate.name}",
                    },
                    evidence={
                        "entity_type": candidate.entity_type,
                        "sample_name": candidate.name,
                        "occurrence_count": candidate.occurrence_count,
                        "sample_proposal_ids": candidate.sample_proposal_ids,
                    },
                    ontology_version=ontology.version,
                    created_at=now,
                    updated_at=now,
                )
            )

        known_relationship_types = set(ontology.relationship_type_ids)
        relationship_items: list[UnmappedRelationshipCandidate] = list(
            state.get("unmapped_relationships") or []
        )
        for rel_candidate in relationship_items:
            if rel_candidate.relationship_type in known_relationship_types:
                continue
            if rel_candidate.occurrence_count < MIN_UNMAPPED_OCCURRENCES:
                continue
            proposals.append(
                OntologyProposal(
                    id=uuid4(),
                    owner_id=owner_id,
                    kind=OntologyProposalKind.RELATIONSHIP_TYPE,
                    status=OntologyProposalStatus.PENDING,
                    title=_title_for_relationship(rel_candidate),
                    rationale=(
                        f"A(z) „{rel_candidate.relationship_type}” kapcsolat "
                        f"{rel_candidate.occurrence_count} alkalommal szerepelt, "
                        "de nincs a normatív ontológiában."
                    ),
                    proposed_definition={
                        "id": rel_candidate.relationship_type,
                        "label": rel_candidate.relationship_type.replace("_", " ").title(),
                        "source_types": ["entity"],
                        "target_types": ["entity"],
                    },
                    evidence={
                        "relationship_type": rel_candidate.relationship_type,
                        "occurrence_count": rel_candidate.occurrence_count,
                        "sample_proposal_ids": rel_candidate.sample_proposal_ids,
                    },
                    ontology_version=ontology.version,
                    created_at=now,
                    updated_at=now,
                )
            )

        return {**state, "proposals": proposals}

    async def persist_proposals_node(state: OntologyCuratorState) -> OntologyCuratorState:
        saved = await persist_proposals(state["owner_id"], list(state.get("proposals", [])))
        return {**state, "proposals": saved}

    graph = StateGraph(OntologyCuratorState)
    graph.add_node("aggregate_unmapped", aggregate_unmapped_node)
    graph.add_node("read_ontology", read_ontology_node)
    graph.add_node("propose_additions", propose_additions_node)
    graph.add_node("persist_proposals", persist_proposals_node)
    graph.set_entry_point("aggregate_unmapped")
    graph.add_edge("aggregate_unmapped", "read_ontology")
    graph.add_edge("read_ontology", "propose_additions")
    graph.add_edge("propose_additions", "persist_proposals")
    graph.add_edge("persist_proposals", END)
    return graph.compile()
