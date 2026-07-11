import json
from pathlib import Path
from uuid import uuid4

import pytest
from agents.report.graph import build_report_graph
from domain.report import ProjectSubgraphData


@pytest.mark.asyncio
async def test_report_graph_formats_golden_project_sections() -> None:
    fixture_path = (
        Path(__file__).resolve().parents[1] / "fixtures" / "projects" / "alpha-report.json"
    )
    payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    subgraph = ProjectSubgraphData.model_validate(payload)

    async def load_subgraph(
        owner_id: object,
        project_entity_id: object,
        start_at: object,
        end_at: object,
    ) -> ProjectSubgraphData:
        _ = (owner_id, project_entity_id, start_at, end_at)
        return subgraph

    graph = build_report_graph(load_subgraph=load_subgraph)
    final = await graph.ainvoke(
        {
            "owner_id": uuid4(),
            "project_entity_id": uuid4(),
            "start_at": None,
            "end_at": None,
        }
    )

    markdown = str(final["markdown"])
    assert "Project Alpha" in markdown
    assert "prioritize local-first deployment" in markdown
    assert "Wire Google OAuth callback" in markdown
    assert "## Kockázatok" in markdown
    assert "## Döntések" in markdown
    assert "## Nyitott feladatok" in markdown
