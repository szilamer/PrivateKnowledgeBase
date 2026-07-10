# Technical Specification

**Version:** 0.2  
**Status:** Approved for MVP implementation subject to accepted ADRs

## 1. Normative technology stack

- Python 3.12+
- FastAPI, Pydantic v2, SQLAlchemy 2.x, Alembic
- PostgreSQL with pgvector
- Neo4j Community Edition
- Redis and Celery
- LangGraph for stateful agent flows
- Next.js and TypeScript
- Docker Compose
- OpenTelemetry-compatible tracing and structured JSON logging

## 2. Repository layout

```text
apps/
  api/
  worker/
  web/
packages/
  domain/
  application/
  adapters/
  agents/
  ontology/
  prompts/
  observability/
tests/
  unit/
  integration/
  contract/
  e2e/
infra/
  docker/
docs/
```

The domain package MUST NOT import FastAPI, Celery, Neo4j drivers, provider SDKs, or UI code.

## 3. API conventions

- Base prefix: `/api/v1`
- JSON request and response bodies
- OpenAPI generated from code and committed or published in CI
- Stable error envelope with `code`, `message`, `details`, and `correlation_id`
- Cursor pagination for large collections
- Idempotency keys for user-triggered long-running operations

Primary resources include `/sources`, `/sync-runs`, `/source-objects`, `/proposals`, `/entities`, `/claims`, `/projects`, `/search`, `/questions`, `/ontology-proposals`, `/audit-events`, and `/health`.

## 4. Persistence

PostgreSQL schemas include identity, sources, ingestion, content, knowledge, approval, ontology metadata, audit, and outbox. Migrations use Alembic. Every row has stable ID and timestamps; mutable aggregates use optimistic versioning where appropriate.

Vectors store embedding model, dimension, content hash, and created time. Mixing incompatible embedding spaces in one index is forbidden.

## 5. Graph projection

Only the projector writes Neo4j. `GraphRepository` exposes bounded traversal, entity neighborhood, claim evidence path, project subgraph, and path search. Cypher statements are parameterized and tested.

## 6. Background jobs

Required Celery queues:

- `ingestion`
- `extraction`
- `embedding`
- `graph_projection`
- `maintenance`

Tasks are idempotent. Transient errors use bounded exponential retry; permanent errors enter a dead-letter state with operator retry.

## 7. Agent integration

LangGraph state schemas are versioned Pydantic models. Tool calls invoke application services, not database clients. All LLM outputs are schema validated. Model, provider, prompt version, schema version, token usage, and latency are recorded.

## 8. Configuration and secrets

Configuration follows environment variables plus non-secret versioned defaults. Secrets are loaded through local secret files or environment injection and MUST NOT be logged or committed.

## 9. Quality gates

CI requires formatting, linting, static type checking, unit tests, integration tests for changed adapters, migration validation, dependency and secret scanning, and OpenAPI compatibility checks.

## 10. Definition of done

A feature is complete only when its requirement ID is linked, tests pass, authorization and audit behavior are implemented, failure modes are documented, migrations are included, and relevant documentation is updated.
