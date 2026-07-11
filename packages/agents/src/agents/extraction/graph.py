from collections.abc import Awaitable, Callable
from typing import Any, Literal
from uuid import UUID

from domain.extraction import ExtractionResult
from domain.extraction_outcome import ExtractionLLMResult
from domain.extraction_validation import validate_extraction_result
from langgraph.graph import END, StateGraph

from agents.extraction.state import ExtractionState


def build_extraction_graph(
    *,
    load_chunks: Callable[[UUID], Awaitable[list[tuple[UUID, str]]]],
    try_llm_extraction: Callable[
        [str, list[tuple[UUID, str]]], Awaitable[ExtractionLLMResult | None]
    ],
    run_heuristic_extraction: Callable[[str, list[tuple[UUID, str]]], ExtractionResult],
    persist_proposals: Callable[[ExtractionState, ExtractionResult], Awaitable[tuple[int, int]]],
    llm_available: bool,
) -> Any:
    """LangGraph extraction flow — prepare → LLM/heuristic → validate → persist (ADR-006)."""

    async def prepare_node(state: ExtractionState) -> ExtractionState:
        version_id = state["version_id"]
        chunks = await load_chunks(version_id)
        full_text = "\n\n".join(text for _, text in chunks)
        return {
            **state,
            "chunks": chunks,
            "full_text": full_text,
            "llm_available": llm_available,
            "fallback_used": False,
            "validation_passed": False,
            "validation_errors": [],
            "requires_review_count": 0,
        }

    async def extract_llm_node(state: ExtractionState) -> ExtractionState:
        llm_result = await try_llm_extraction(
            state.get("full_text", ""),
            state.get("chunks", []),
        )
        if llm_result is None:
            return {**state, "llm_error": "llm_unavailable"}
        return {
            **state,
            "extraction": llm_result.result,
            "provider": "llm",
            "token_usage": llm_result.token_usage,
            "fallback_used": False,
            "llm_error": None,
        }

    async def extract_heuristic_node(state: ExtractionState) -> ExtractionState:
        extraction = run_heuristic_extraction(
            state.get("full_text", ""),
            state.get("chunks", []),
        )
        fallback = state.get("provider") == "llm" or bool(state.get("llm_error"))
        return {
            **state,
            "extraction": extraction,
            "provider": "heuristic",
            "fallback_used": fallback,
            "token_usage": state.get("token_usage"),
        }

    async def validate_node(state: ExtractionState) -> ExtractionState:
        extraction = state.get("extraction")
        if extraction is None:
            return {
                **state,
                "validation_passed": False,
                "validation_errors": ["no extraction result"],
                "error": "no extraction result",
            }
        passed, errors = validate_extraction_result(extraction)
        return {
            **state,
            "validation_passed": passed,
            "validation_errors": errors,
            "error": None if passed else "; ".join(errors[:5]),
        }

    async def persist_node(state: ExtractionState) -> ExtractionState:
        extraction = state.get("extraction")
        if extraction is None:
            return {**state, "proposal_count": 0, "requires_review_count": 0}
        count, review_count = await persist_proposals(state, extraction)
        return {
            **state,
            "proposal_count": count,
            "requires_review_count": review_count,
        }

    def route_after_prepare(
        state: ExtractionState,
    ) -> Literal["extract_llm", "extract_heuristic"]:
        if state.get("llm_available"):
            return "extract_llm"
        return "extract_heuristic"

    def route_after_llm(
        state: ExtractionState,
    ) -> Literal["validate", "extract_heuristic"]:
        if state.get("extraction") is not None:
            return "validate"
        return "extract_heuristic"

    def route_after_validate(state: ExtractionState) -> Literal["persist", "done"]:
        if state.get("validation_passed"):
            return "persist"
        return "done"

    graph = StateGraph(ExtractionState)
    graph.add_node("prepare", prepare_node)
    graph.add_node("extract_llm", extract_llm_node)
    graph.add_node("extract_heuristic", extract_heuristic_node)
    graph.add_node("validate", validate_node)
    graph.add_node("persist", persist_node)
    graph.set_entry_point("prepare")
    graph.add_conditional_edges("prepare", route_after_prepare)
    graph.add_conditional_edges("extract_llm", route_after_llm)
    graph.add_edge("extract_heuristic", "validate")
    graph.add_conditional_edges(
        "validate",
        route_after_validate,
        {"persist": "persist", "done": END},
    )
    graph.add_edge("persist", END)
    return graph.compile()
