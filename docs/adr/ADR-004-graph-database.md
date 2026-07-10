# ADR-004: Graph Database

**Status:** Accepted  
**Decision date:** 2026-07-10

## Decision

The MVP uses Neo4j Community Edition as its native graph database. Application code accesses it only through `GraphRepository`. Neo4j stores projected entity nodes, typed relationships, claim-source and claim-entity links, temporal and provenance links, and runtime ontology instances. PostgreSQL remains the transactional source of truth; Neo4j is a query projection updated through a transactional outbox.

## Consequences

Eventual consistency is accepted with an observable lag target. The projection can be rebuilt from PostgreSQL. Direct Neo4j writes are permitted only from the projection component.
