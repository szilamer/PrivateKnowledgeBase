"""Contradiction detection LangGraph agent (Phase D)."""

from agents.contradiction.graph import build_contradiction_graph
from agents.contradiction.state import ContradictionState

__all__ = ["ContradictionState", "build_contradiction_graph"]
