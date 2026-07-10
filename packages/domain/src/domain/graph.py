from uuid import UUID

from pydantic import BaseModel, Field


class GraphNode(BaseModel):
    id: str
    label: str
    node_type: str
    properties: dict[str, object] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    id: str
    source_id: str
    target_id: str
    edge_type: str
    properties: dict[str, object] = Field(default_factory=dict)


class GraphView(BaseModel):
    root_id: UUID | None = None
    depth: int = 1
    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)
    truncated: bool = False
