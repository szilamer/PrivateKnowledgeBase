from collections.abc import Awaitable, Callable
from datetime import datetime
from typing import Any
from uuid import UUID

from domain.canonical import CanonicalClaim
from domain.contradiction_detection import compare_claim_against_candidates
from domain.contradiction_outcome import CONTRADICTION_PIPELINE_VERSION
from langgraph.graph import END, StateGraph

from agents.contradiction.state import ContradictionState


def build_contradiction_graph(
    *,
    load_candidate_claims: Callable[[UUID, UUID | None, str], Awaitable[list[CanonicalClaim]]],
    now: datetime,
) -> Any:
    """LangGraph contradiction flow — load candidates → compare → findings (ADR-006)."""

    async def load_candidates_node(state: ContradictionState) -> ContradictionState:
        claim = state["claim"]
        owner_id = state["owner_id"]
        candidates = await load_candidate_claims(
            owner_id,
            claim.subject_entity_id,
            claim.predicate,
        )
        return {
            **state,
            "candidates": candidates,
            "candidate_count": len(candidates),
            "pipeline_version": CONTRADICTION_PIPELINE_VERSION,
        }

    async def compare_node(state: ContradictionState) -> ContradictionState:
        claim = state["claim"]
        proposal = state["proposal"]
        owner_id = state["owner_id"]
        candidates = state.get("candidates", [])
        findings = compare_claim_against_candidates(
            owner_id=owner_id,
            new_claim=claim,
            candidates=candidates,
            proposal=proposal,
            now=now,
        )
        return {**state, "findings": findings}

    graph = StateGraph(ContradictionState)
    graph.add_node("load_candidate_claims", load_candidates_node)
    graph.add_node("compare", compare_node)
    graph.set_entry_point("load_candidate_claims")
    graph.add_edge("load_candidate_claims", "compare")
    graph.add_edge("compare", END)
    return graph.compile()
