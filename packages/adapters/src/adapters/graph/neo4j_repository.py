from uuid import UUID

from domain.graph import GraphEdge, GraphNode, GraphView

from adapters.graph.projector import Neo4jSettings


class Neo4jGraphRepository:
    """Read-only graph access for API queries."""

    def __init__(self, settings: Neo4jSettings) -> None:
        from neo4j import AsyncGraphDatabase

        self._driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )

    async def close(self) -> None:
        await self._driver.close()

    async def get_entity_neighborhood(
        self,
        owner_id: UUID,
        entity_id: UUID,
        *,
        depth: int = 1,
        limit: int = 50,
    ) -> GraphView:
        return await self._query_subgraph(
            owner_id=owner_id,
            root_entity_id=entity_id,
            depth=depth,
            limit=limit,
        )

    async def get_bounded_subgraph(
        self,
        owner_id: UUID,
        *,
        root_entity_id: UUID | None = None,
        depth: int = 2,
        limit: int = 100,
    ) -> GraphView:
        return await self._query_subgraph(
            owner_id=owner_id,
            root_entity_id=root_entity_id,
            depth=depth,
            limit=limit,
        )

    async def _query_subgraph(
        self,
        *,
        owner_id: UUID,
        root_entity_id: UUID | None,
        depth: int,
        limit: int,
    ) -> GraphView:
        nodes: dict[str, GraphNode] = {}
        edges: list[GraphEdge] = []
        truncated = False

        async with self._driver.session() as session:
            if root_entity_id:
                entity_result = await session.run(
                    """
                    MATCH (e:Entity {id: $entity_id, owner_id: $owner_id})
                    RETURN e
                    LIMIT 1
                    """,
                    entity_id=str(root_entity_id),
                    owner_id=str(owner_id),
                )
                entity_record = await entity_result.single()
                if entity_record:
                    entity = dict(entity_record["e"])
                    nodes[str(entity["id"])] = GraphNode(
                        id=str(entity["id"]),
                        label=str(entity.get("name", "Entity")),
                        node_type="entity",
                        properties={
                            "entity_type": entity.get("entity_type"),
                            "aliases": entity.get("aliases", []),
                        },
                    )

                rel_result = await session.run(
                    """
                    MATCH (e:Entity {id: $entity_id, owner_id: $owner_id})
                    OPTIONAL MATCH (e)-[r]-(n)
                    WHERE n:Entity OR n:Claim
                    RETURN r AS rel, startNode(r) AS source, endNode(r) AS target
                    LIMIT $limit
                    """,
                    entity_id=str(root_entity_id),
                    owner_id=str(owner_id),
                    limit=limit + 1,
                )
            else:
                rel_result = await session.run(
                    """
                    MATCH (e:Entity {owner_id: $owner_id})
                    OPTIONAL MATCH (e)-[r]-(n)
                    WHERE n:Entity OR n:Claim
                    RETURN DISTINCT r AS rel, startNode(r) AS source, endNode(r) AS target
                    LIMIT $limit
                    """,
                    owner_id=str(owner_id),
                    limit=limit + 1,
                )

            count = 0
            async for record in rel_result:
                count += 1
                if count > limit:
                    truncated = True
                    break
                rel = record.get("rel")
                source = record.get("source")
                target = record.get("target")
                if rel is None or source is None or target is None:
                    continue
                source_props = dict(source)
                target_props = dict(target)
                source_id = str(source_props["id"])
                target_id = str(target_props["id"])
                source_label = str(source_props.get("name", source_props.get("predicate", "Node")))
                target_label = str(target_props.get("name", target_props.get("predicate", "Node")))
                source_type = "entity" if "entity_type" in source_props else "claim"
                target_type = "entity" if "entity_type" in target_props else "claim"
                nodes[source_id] = GraphNode(
                    id=source_id,
                    label=source_label,
                    node_type=source_type,
                    properties=source_props,
                )
                nodes[target_id] = GraphNode(
                    id=target_id,
                    label=target_label,
                    node_type=target_type,
                    properties=target_props,
                )
                rel_props = dict(rel)
                edges.append(
                    GraphEdge(
                        id=str(rel_props.get("id", f"{source_id}-{target_id}")),
                        source_id=source_id,
                        target_id=target_id,
                        edge_type=rel.type,
                        properties=rel_props,
                    )
                )

        return GraphView(
            root_id=root_entity_id,
            depth=depth,
            nodes=list(nodes.values()),
            edges=edges,
            truncated=truncated,
        )
