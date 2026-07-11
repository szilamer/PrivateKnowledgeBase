from typing import Any

from domain.triage import TRIAGE_PIPELINE_VERSION, classify_version_metadata
from langgraph.graph import END, StateGraph

from agents.triage.state import TriageState


def build_triage_graph() -> Any:
    """LangGraph triage — load metadata → deterministic classify (ADR-006)."""

    async def load_metadata_node(state: TriageState) -> TriageState:
        return {**state, "pipeline_version": TRIAGE_PIPELINE_VERSION}

    async def classify_node(state: TriageState) -> TriageState:
        classification = classify_version_metadata(
            external_id=state["external_id"],
            mime_type=state.get("mime_type"),
            source_configuration=state.get("source_configuration"),
        )
        return {**state, "classification": classification}

    graph = StateGraph(TriageState)
    graph.add_node("load_metadata", load_metadata_node)
    graph.add_node("classify", classify_node)
    graph.set_entry_point("load_metadata")
    graph.add_edge("load_metadata", "classify")
    graph.add_edge("classify", END)
    return graph.compile()
