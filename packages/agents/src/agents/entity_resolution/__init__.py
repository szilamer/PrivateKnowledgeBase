"""Entity resolution LangGraph agent (Phase C)."""

from agents.entity_resolution.graph import build_entity_resolution_graph
from agents.entity_resolution.state import EntityResolutionState

__all__ = ["EntityResolutionState", "build_entity_resolution_graph"]
