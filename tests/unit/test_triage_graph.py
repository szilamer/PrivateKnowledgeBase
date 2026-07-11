from uuid import uuid4

import pytest
from agents.triage.graph import build_triage_graph
from domain.triage import TriageSensitivity


@pytest.mark.asyncio
async def test_triage_graph_classifies_markdown() -> None:
    graph = build_triage_graph()
    final = await graph.ainvoke(
        {
            "version_id": uuid4(),
            "external_id": "notes/guide.md",
            "mime_type": "text/markdown",
            "source_configuration": {"default_project": "Atlas"},
        }
    )
    classification = final["classification"]
    assert classification.extractor_hint == "markdown"
    assert classification.relevance >= 0.9
    assert classification.sensitivity == TriageSensitivity.LOW
    assert classification.project_hint == "Atlas"
