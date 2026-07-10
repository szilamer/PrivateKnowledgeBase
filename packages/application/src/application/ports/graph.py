from typing import Protocol
from uuid import UUID

from domain.graph import GraphView


class GraphRepository(Protocol):
    async def get_entity_neighborhood(
        self,
        owner_id: UUID,
        entity_id: UUID,
        *,
        depth: int = 1,
        limit: int = 50,
    ) -> GraphView: ...

    async def get_bounded_subgraph(
        self,
        owner_id: UUID,
        *,
        root_entity_id: UUID | None = None,
        depth: int = 2,
        limit: int = 100,
    ) -> GraphView: ...
