from collections.abc import Awaitable, Callable
from datetime import datetime
from typing import Any
from uuid import UUID

from domain.report import PROJECT_REPORT_PIPELINE_VERSION, ProjectSubgraphData
from langgraph.graph import END, StateGraph

from agents.report.state import ReportState


def _format_period(start_at: datetime | None, end_at: datetime | None) -> str:
    if start_at and end_at:
        return f"{start_at.date()} – {end_at.date()}"
    if start_at:
        return f"{start_at.date()} óta"
    if end_at:
        return f"{end_at.date()}-ig"
    return "teljes időszak"


def _bullet_section(title: str, items: list[str]) -> str:
    if not items:
        return f"## {title}\n\n_Nincs rögzített tétel._\n"
    lines = "\n".join(f"- {item}" for item in items)
    return f"## {title}\n\n{lines}\n"


def build_report_graph(
    *,
    load_subgraph: Callable[
        [UUID, UUID, datetime | None, datetime | None], Awaitable[ProjectSubgraphData]
    ],
) -> Any:
    """LangGraph project report — load subgraph → summarize → format markdown."""

    async def load_project_subgraph_node(state: ReportState) -> ReportState:
        subgraph = await load_subgraph(
            state["owner_id"],
            state["project_entity_id"],
            state.get("start_at"),
            state.get("end_at"),
        )
        return {
            **state,
            "subgraph": subgraph,
            "pipeline_version": PROJECT_REPORT_PIPELINE_VERSION,
        }

    async def summarize_changes_node(state: ReportState) -> ReportState:
        subgraph = state["subgraph"]
        summary = (
            f"A(z) „{subgraph.project_name}” projekthez "
            f"{len(subgraph.decisions)} döntés, {len(subgraph.tasks)} feladat, "
            f"{len(subgraph.events)} esemény és {len(subgraph.risks)} kockázat "
            f"tartozik a kiválasztott időszakban."
        )
        return {**state, "summary": summary}

    async def format_report_node(state: ReportState) -> ReportState:
        subgraph = state["subgraph"]
        period = _format_period(state.get("start_at"), state.get("end_at"))
        title = f"Projektjelentés: {subgraph.project_name}"
        changes = [*subgraph.events]
        if subgraph.technologies:
            changes.append(f"Technológiák: {', '.join(subgraph.technologies)}")
        markdown = (
            f"# {title}\n\n"
            f"**Időszak:** {period}\n\n"
            f"## Összefoglaló\n\n{state.get('summary', '')}\n\n"
            f"{_bullet_section('Változások', changes)}"
            f"{_bullet_section('Kockázatok', subgraph.risks)}"
            f"{_bullet_section('Döntések', subgraph.decisions)}"
            f"{_bullet_section('Nyitott feladatok', subgraph.tasks)}"
        )
        if subgraph.citations:
            citation_lines = "\n".join(f"- {item}" for item in subgraph.citations)
            markdown += f"## Hivatkozások\n\n{citation_lines}\n"
        return {**state, "title": title, "markdown": markdown}

    graph = StateGraph(ReportState)
    graph.add_node("load_project_subgraph", load_project_subgraph_node)
    graph.add_node("summarize_changes", summarize_changes_node)
    graph.add_node("format_report", format_report_node)
    graph.set_entry_point("load_project_subgraph")
    graph.add_edge("load_project_subgraph", "summarize_changes")
    graph.add_edge("summarize_changes", "format_report")
    graph.add_edge("format_report", END)
    return graph.compile()
