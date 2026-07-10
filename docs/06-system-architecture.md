# System Architecture

**Version:** 0.1  
**Status:** Draft

## 1. Architectural style

The MVP is a modular monolith with asynchronous workers and separate infrastructure services. Module boundaries are explicit so components may later be separated without rewriting the domain model.

## 2. Runtime components

- **Web client:** Next.js user interface.
- **API service:** FastAPI application and use-case boundary.
- **Worker service:** Celery workers for ingestion, extraction, embedding, projection, and maintenance.
- **PostgreSQL:** transactional source of truth and pgvector store.
- **Neo4j:** rebuildable graph query projection.
- **Redis:** Celery broker and short-lived coordination.
- **LLM/embedding adapters:** local or cloud provider endpoints selected by policy.
- **Source connectors:** local file and GitHub adapters for the MVP.

## 3. Logical modules

- identity and access
- source registry
- ingestion
- document processing
- knowledge proposals
- approval workflow
- ontology
- retrieval
- graph projection
- question answering
- project reporting
- audit and observability

## 4. Data ownership

PostgreSQL owns transactional state. Neo4j is a query projection populated through an outbox-driven projector. Original files remain in their source location or an explicitly configured immutable object store/reference scheme.

## 5. Main flow

```text
Source connector
  → ingestion record
  → parser
  → source object version
  → chunks
  → embeddings
  → extraction proposal
  → validation / approval
  → canonical knowledge
  → outbox
  → Neo4j projection
```

## 6. Consistency

PostgreSQL commits canonical changes and outbox events atomically. Neo4j is eventually consistent. Projection lag is observable and the projection can be rebuilt from PostgreSQL.

## 7. Security boundaries

All API and worker use cases call the policy service. Retrieval queries include ownership, visibility, and sensitivity constraints. Provider policy decides whether content may leave the local environment.

## 8. Deployment

The MVP runs through Docker Compose with persistent volumes, explicit environment configuration, health checks, and documented backup and restore procedures.

## 9. Extensibility

Connectors, parsers, graph storage, vector retrieval, LLM providers, embedding providers, task dispatch, and graph visualization are hidden behind adapters.
