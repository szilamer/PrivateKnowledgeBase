from collections.abc import Awaitable, Callable
from typing import Any
from uuid import UUID

from domain.entities import EntityMatch
from domain.entity_resolution import build_entity_resolution_spec, resolve_entity
from domain.entity_resolution_outcome import ENTITY_RESOLUTION_PIPELINE_VERSION
from langgraph.graph import END, StateGraph

from agents.entity_resolution.state import EntityResolutionState


def build_entity_resolution_graph(
    *,
    find_matches: Callable[[UUID, str, str], Awaitable[list[EntityMatch]]],
) -> Any:
    """LangGraph entity resolution — retrieve candidates → deterministic resolve (ADR-006)."""

    async def retrieve_candidates_node(state: EntityResolutionState) -> EntityResolutionState:
        entity = state["entity"]
        owner_id = state["owner_id"]
        candidates = await find_matches(
            owner_id,
            entity.name,
            entity.entity_type.value,
        )
        return {
            **state,
            "candidates": candidates,
            "pipeline_version": ENTITY_RESOLUTION_PIPELINE_VERSION,
        }

    async def resolve_node(state: EntityResolutionState) -> EntityResolutionState:
        entity = state["entity"]
        candidates = state.get("candidates", [])
        action, resolution_matches = resolve_entity(entity, candidates)
        spec = build_entity_resolution_spec(entity, action, resolution_matches)
        return {
            **state,
            "resolution_action": spec.resolution_action,
            "resolution_matches": resolution_matches,
            "proposal_type": spec.proposal_type.value,
            "payload": spec.payload,
            "needs_review": spec.needs_review,
            "risk_level": spec.risk_level,
        }

    graph = StateGraph(EntityResolutionState)
    graph.add_node("retrieve_candidates", retrieve_candidates_node)
    graph.add_node("resolve", resolve_node)
    graph.set_entry_point("retrieve_candidates")
    graph.add_edge("retrieve_candidates", "resolve")
    graph.add_edge("resolve", END)
    return graph.compile()
