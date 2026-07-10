from collections.abc import Awaitable, Callable
from typing import Any
from uuid import UUID

from domain.extraction import ExtractionResult
from langgraph.graph import END, StateGraph

from agents.extraction.state import ExtractionState


async def _noop(state: ExtractionState) -> ExtractionState:
    return state


def build_extraction_graph(
    *,
    load_chunks: Callable[[UUID], Awaitable[list[tuple[UUID, str]]]],
    run_extraction: Callable[[str, list[tuple[UUID, str]]], Awaitable[ExtractionResult]],
    persist_proposals: Callable[[ExtractionState, ExtractionResult], Awaitable[int]],
) -> Any:
    """LangGraph extraction flow — orchestration only (ADR-006)."""

    async def prepare_node(state: ExtractionState) -> ExtractionState:
        version_id = state["version_id"]
        chunks = await load_chunks(version_id)
        full_text = "\n\n".join(text for _, text in chunks)
        return {**state, "chunks": chunks, "full_text": full_text}

    async def extract_node(state: ExtractionState) -> ExtractionState:
        extraction = await run_extraction(state.get("full_text", ""), state.get("chunks", []))
        return {**state, "extraction": extraction}

    async def persist_node(state: ExtractionState) -> ExtractionState:
        extraction = state.get("extraction")
        if extraction is None:
            return {**state, "proposal_count": 0}
        count = await persist_proposals(state, extraction)
        return {**state, "proposal_count": count}

    graph = StateGraph(ExtractionState)
    graph.add_node("prepare", prepare_node)
    graph.add_node("extract", extract_node)
    graph.add_node("persist", persist_node)
    graph.set_entry_point("prepare")
    graph.add_edge("prepare", "extract")
    graph.add_edge("extract", "persist")
    graph.add_edge("persist", END)
    return graph.compile()
