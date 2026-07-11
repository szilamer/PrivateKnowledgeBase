from collections.abc import Awaitable, Callable
from typing import Any

from domain.questions import Citation
from domain.synthesis_outcome import SYNTHESIS_PIPELINE_VERSION, SynthesisDraft
from domain.synthesis_validation import detect_citation_conflicts, validate_claim_citations
from langgraph.graph import END, StateGraph

from agents.synthesis.state import SynthesisState


def build_synthesis_graph(
    *,
    synthesize_draft: Callable[[str, dict[str, str], list[Citation]], Awaitable[SynthesisDraft]],
) -> Any:
    """LangGraph answer synthesis — build context → synthesize → validate citations."""

    async def build_context_node(state: SynthesisState) -> SynthesisState:
        citations = state["citations"]
        context_package = {citation.citation_id: citation.excerpt[:600] for citation in citations}
        return {
            **state,
            "context_package": context_package,
            "allowed_citation_ids": list(context_package.keys()),
            "pipeline_version": SYNTHESIS_PIPELINE_VERSION,
        }

    async def synthesize_node(state: SynthesisState) -> SynthesisState:
        draft = await synthesize_draft(
            state["question"],
            state.get("context_package", {}),
            state["citations"],
        )
        return {
            **state,
            "draft": draft,
            "answer": draft.answer,
            "confidence": draft.confidence,
            "insufficient_evidence": draft.insufficient_evidence,
            "claims": draft.claims,
            "warnings": list(draft.warnings),
            "conflicts": list(draft.conflicts),
            "model": draft.model,
        }

    async def validate_citations_node(state: SynthesisState) -> SynthesisState:
        allowed = set(state.get("allowed_citation_ids", []))
        claims, citation_warnings = validate_claim_citations(
            list(state.get("claims", [])),
            allowed,
        )
        conflict_notes = detect_citation_conflicts(state["citations"])
        warnings = list(state.get("warnings", [])) + citation_warnings
        conflicts = list(dict.fromkeys([*state.get("conflicts", []), *conflict_notes]))
        return {
            **state,
            "claims": claims,
            "warnings": warnings,
            "conflicts": conflicts,
            "validation_passed": True,
        }

    graph = StateGraph(SynthesisState)
    graph.add_node("build_context", build_context_node)
    graph.add_node("synthesize", synthesize_node)
    graph.add_node("validate_citations", validate_citations_node)
    graph.set_entry_point("build_context")
    graph.add_edge("build_context", "synthesize")
    graph.add_edge("synthesize", "validate_citations")
    graph.add_edge("validate_citations", END)
    return graph.compile()
