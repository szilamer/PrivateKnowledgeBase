from collections.abc import Awaitable, Callable
from typing import Any
from uuid import UUID

from domain.canonical import CanonicalClaim, CanonicalEntity
from domain.content import ChunkSearchHit
from domain.graph import GraphView
from domain.questions import Citation, RetrievalPlanStep, RetrievalSignal
from domain.retrieval import add_chunk_citation
from domain.retrieval_outcome import RETRIEVAL_PIPELINE_VERSION
from langgraph.graph import END, StateGraph

from agents.retrieval.state import RetrievalState


def build_retrieval_graph(
    *,
    search_chunks: Callable[[UUID, str, str, int], Awaitable[list[ChunkSearchHit]]],
    find_matching_entities: Callable[[UUID, str], Awaitable[list[CanonicalEntity]]],
    expand_neighborhood: Callable[[UUID, UUID], Awaitable[GraphView]],
    search_claims: Callable[[UUID, str, int], Awaitable[list[CanonicalClaim]]],
) -> Any:
    """LangGraph retrieval planner — search → graph → canonical → rank (ADR-006)."""

    async def search_chunks_node(state: RetrievalState) -> RetrievalState:
        owner_id = state["owner_id"]
        question = state["question"]
        mode = state["mode"]
        limit = state["limit"]
        hits = await search_chunks(owner_id, question, mode, limit)
        citations = dict(state.get("citations", {}))
        plan = list(state.get("plan", []))
        signal = (
            RetrievalSignal.KEYWORD
            if mode == "keyword"
            else RetrievalSignal.SEMANTIC
            if mode == "semantic"
            else RetrievalSignal.KEYWORD
        )
        for hit in hits:
            add_chunk_citation(citations, hit, signal=signal)
        plan.append(
            RetrievalPlanStep(
                signal=signal if mode != "hybrid" else RetrievalSignal.KEYWORD,
                description=f"{mode} chunk search",
                result_count=len(hits),
            )
        )
        return {
            **state,
            "citations": citations,
            "plan": plan,
            "pipeline_version": RETRIEVAL_PIPELINE_VERSION,
        }

    async def expand_graph_node(state: RetrievalState) -> RetrievalState:
        owner_id = state["owner_id"]
        question = state["question"]
        citations = dict(state.get("citations", {}))
        plan = list(state.get("plan", []))
        related_entities = list(state.get("related_entities", []))
        matching_entities = await find_matching_entities(owner_id, question)
        for entity in matching_entities:
            related_entities.append(entity.id)
            graph_view = await expand_neighborhood(owner_id, entity.id)
            for node in graph_view.nodes:
                if node.node_type == "entity":
                    citations[f"graph-{node.id}"] = Citation(
                        citation_id=f"graph-{node.id}",
                        excerpt=f"Graph entity: {node.label}",
                        score=0.5,
                        signal=RetrievalSignal.GRAPH,
                    )
        plan.append(
            RetrievalPlanStep(
                signal=RetrievalSignal.GRAPH,
                description="entity neighborhood expansion",
                result_count=len(matching_entities),
            )
        )
        return {
            **state,
            "citations": citations,
            "plan": plan,
            "related_entities": related_entities,
        }

    async def lookup_canonical_node(state: RetrievalState) -> RetrievalState:
        owner_id = state["owner_id"]
        question = state["question"]
        limit = state["limit"]
        citations = dict(state.get("citations", {}))
        plan = list(state.get("plan", []))
        related_entities = list(state.get("related_entities", []))
        claims = await search_claims(owner_id, question, limit)
        for claim in claims:
            cite_id = f"claim-{claim.id}"
            citations[cite_id] = Citation(
                citation_id=cite_id,
                excerpt=f"{claim.predicate}: {claim.object_value}",
                score=float(claim.confidence),
                signal=RetrievalSignal.CANONICAL,
            )
            if claim.subject_entity_id:
                related_entities.append(claim.subject_entity_id)
        plan.append(
            RetrievalPlanStep(
                signal=RetrievalSignal.CANONICAL,
                description="canonical claim lookup",
                result_count=len(claims),
            )
        )
        return {
            **state,
            "citations": citations,
            "plan": plan,
            "related_entities": related_entities,
        }

    async def rank_citations_node(state: RetrievalState) -> RetrievalState:
        limit = state["limit"]
        citations = state.get("citations", {})
        ranked = sorted(citations.values(), key=lambda item: item.score, reverse=True)[:limit]
        related_entities = list(dict.fromkeys(state.get("related_entities", [])))
        return {
            **state,
            "citations": {item.citation_id: item for item in ranked},
            "citation_ids": [item.citation_id for item in ranked],
            "related_entities": related_entities,
        }

    graph = StateGraph(RetrievalState)
    graph.add_node("search_chunks", search_chunks_node)
    graph.add_node("expand_graph", expand_graph_node)
    graph.add_node("lookup_canonical", lookup_canonical_node)
    graph.add_node("rank_citations", rank_citations_node)
    graph.set_entry_point("search_chunks")
    graph.add_edge("search_chunks", "expand_graph")
    graph.add_edge("expand_graph", "lookup_canonical")
    graph.add_edge("lookup_canonical", "rank_citations")
    graph.add_edge("rank_citations", END)
    return graph.compile()
