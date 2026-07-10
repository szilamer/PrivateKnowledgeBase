import re
from typing import Protocol

from domain.canonical import OutboxEvent


class Neo4jSettings(Protocol):
    neo4j_uri: str
    neo4j_user: str
    neo4j_password: str


class Neo4jGraphProjector:
    """Only component allowed to write Neo4j (ADR-004)."""

    def __init__(self, settings: Neo4jSettings) -> None:
        from neo4j import AsyncGraphDatabase

        self._driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )

    async def close(self) -> None:
        await self._driver.close()

    async def ensure_constraints(self) -> None:
        async with self._driver.session() as session:
            await session.run(
                "CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE"
            )
            await session.run(
                "CREATE CONSTRAINT claim_id IF NOT EXISTS FOR (c:Claim) REQUIRE c.id IS UNIQUE"
            )

    async def project_event(self, event: OutboxEvent) -> None:
        handlers = {
            "entity.materialized": self._project_entity,
            "relationship.materialized": self._project_relationship,
            "claim.materialized": self._project_claim,
            "contradiction.detected": self._project_contradiction,
        }
        handler = handlers.get(event.event_type)
        if handler is None:
            return
        await handler(event.payload)

    async def _project_entity(self, payload: dict[str, object]) -> None:
        async with self._driver.session() as session:
            await session.run(
                """
                MERGE (e:Entity {id: $id})
                SET e.owner_id = $owner_id,
                    e.entity_type = $entity_type,
                    e.name = $name,
                    e.aliases = $aliases
                """,
                id=str(payload["entity_id"]),
                owner_id=str(payload["owner_id"]),
                entity_type=str(payload["entity_type"]),
                name=str(payload["canonical_name"]),
                aliases=payload.get("aliases", []),
            )

    async def _project_relationship(self, payload: dict[str, object]) -> None:
        raw_type = str(payload.get("relationship_type", "RELATES_TO"))
        rel_type = re.sub(r"[^A-Z0-9_]", "_", raw_type.upper())
        async with self._driver.session() as session:
            await session.run(
                f"""
                MATCH (source:Entity {{id: $source_id}})
                MATCH (target:Entity {{id: $target_id}})
                MERGE (source)-[r:{rel_type} {{id: $relationship_id}}]->(target)
                SET r.owner_id = $owner_id
                """,
                source_id=str(payload["source_entity_id"]),
                target_id=str(payload["target_entity_id"]),
                relationship_id=str(payload["relationship_id"]),
                owner_id=str(payload["owner_id"]),
            )

    async def _project_claim(self, payload: dict[str, object]) -> None:
        async with self._driver.session() as session:
            await session.run(
                """
                MERGE (c:Claim {id: $id})
                SET c.owner_id = $owner_id,
                    c.predicate = $predicate,
                    c.object_value = $object_value,
                    c.status = $status,
                    c.confidence = $confidence
                """,
                id=str(payload["claim_id"]),
                owner_id=str(payload["owner_id"]),
                predicate=str(payload["predicate"]),
                object_value=str(payload["object_value"]),
                status=str(payload.get("status", "active")),
                confidence=float(str(payload.get("confidence", 0.0))),
            )
            subject_id = payload.get("subject_entity_id")
            if subject_id:
                await session.run(
                    """
                    MATCH (e:Entity {id: $entity_id})
                    MATCH (c:Claim {id: $claim_id})
                    MERGE (e)-[:HAS_CLAIM]->(c)
                    """,
                    entity_id=str(subject_id),
                    claim_id=str(payload["claim_id"]),
                )

    async def _project_contradiction(self, payload: dict[str, object]) -> None:
        async with self._driver.session() as session:
            await session.run(
                """
                MATCH (existing:Claim {id: $existing_claim_id})
                MERGE (f:ContradictionFinding {id: $finding_id})
                SET f.summary = $summary, f.owner_id = $owner_id
                MERGE (f)-[:CONTRADICTS]->(existing)
                """,
                existing_claim_id=str(payload["existing_claim_id"]),
                finding_id=str(payload["finding_id"]),
                summary=str(payload["summary"]),
                owner_id=str(payload["owner_id"]),
            )
