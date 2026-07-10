# ADR-003: Primary Metadata and Vector Store

**Status:** Accepted  
**Decision date:** 2026-07-10

## Decision

PostgreSQL is the primary transactional and metadata store. Chunk embeddings are stored in the same database using pgvector. PostgreSQL contains sources, source objects, ingestion runs, pipeline versions, document versions, content hashes, chunks, embeddings, proposals, approvals, users, policies, audit metadata, and outbox events.

## Rationale

This reduces MVP operational complexity and keeps metadata and vector indexing transactionally close.

## Consequences

Vector search must support authorization and project filters. A repository interface isolates future vector-store replacement. Each embedding record stores the model identifier.
