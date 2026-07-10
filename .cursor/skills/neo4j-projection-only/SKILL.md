---
name: neo4j-projection-only
description: Implement Neo4j graph reads or projection writes following the outbox pattern. Use when working with GraphRepository, Cypher queries, or graph browser features.
---

# Neo4j Projection Only

Per ADR-004 and `docs/07-technical-specification.md` §5.

## Rules

- PostgreSQL is source of truth; Neo4j is rebuildable query projection
- **Only the projector** writes to Neo4j (via outbox-driven `graph_projection` queue)
- Application code uses `GraphRepository` — never raw Neo4j driver elsewhere
- Cypher always parameterized; tested in integration tests
- Eventual consistency accepted; projection lag must be observable

## GraphRepository operations

- Bounded traversal
- Entity neighborhood
- Claim evidence path
- Project subgraph
- Path search

## Rebuild

Projection must be rebuildable from PostgreSQL outbox + canonical data.

## Do not

- Add direct Neo4j writes in API routes, workers (except projector), or agents
- Store durable business state only in Neo4j
