# Technology Decisions and ADR Index

**Version:** 1.0  
**Status:** Approved and normative  
**Decision date:** 2026-07-10

## 1. Purpose

This document is the authoritative index of technology and architecture decisions for the MVP. A developer or code-generation agent MUST follow accepted ADRs and MUST NOT independently substitute a technology.

## 2. Normative stack

| Area | Decision |
|---|---|
| Runtime | Local-first Docker Compose |
| Backend | Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy 2.x, Alembic |
| Metadata store | PostgreSQL |
| Vector search | pgvector |
| Graph database | Neo4j Community Edition |
| Background jobs | Redis + Celery |
| Agent orchestration | LangGraph |
| LLM/embeddings | Provider-independent interfaces; cloud and local OpenAI-compatible endpoints |
| Frontend | Next.js + TypeScript |
| Authentication | Local single-user session with future provider interface |
| Ontology | Version-controlled YAML, projected at runtime |
| Observability | Structured JSON logs + OpenTelemetry-compatible tracing |

## 3. ADR index

- [ADR-001 Runtime and Deployment Model](adr/ADR-001-runtime-and-deployment-model.md)
- [ADR-002 Backend and API](adr/ADR-002-backend-and-api.md)
- [ADR-003 PostgreSQL and pgvector](adr/ADR-003-postgresql-and-pgvector.md)
- [ADR-004 Graph Database](adr/ADR-004-graph-database.md)
- [ADR-005 Background Jobs](adr/ADR-005-background-jobs.md)
- [ADR-006 Agent Orchestration](adr/ADR-006-agent-orchestration.md)
- [ADR-007 LLM and Embedding Strategy](adr/ADR-007-llm-and-embedding-strategy.md)
- [ADR-008 Frontend](adr/ADR-008-frontend.md)
- [ADR-009 Authentication and Authorization](adr/ADR-009-authentication-and-authorization.md)
- [ADR-010 Document Processing](adr/ADR-010-document-processing.md)
- [ADR-011 Ontology Storage](adr/ADR-011-ontology-storage.md)
- [ADR-012 Observability and Audit](adr/ADR-012-observability-and-audit.md)
- [ADR-013 Google Workspace Connectors](adr/ADR-013-google-workspace-connectors.md) — **Proposed**

## 4. Specification supplements (post-MVP)

- [13 — Personal Source Connectors](13-personal-source-connectors-supplement.md)
- [14 — Source Connection UI](14-source-connection-ui-supplement.md)

## 5. Precedence

1. Accepted ADRs
2. Technical specification
3. System architecture
4. Domain model and ontology
5. Functional specification
6. MVP scope and product requirements
7. Project vision and concept
8. Approved specification supplements (`docs/13-*`, `docs/14-*`)

## 6. Change process

A technology decision may change only through a new or superseding ADR. The ADR must document context, decision drivers, alternatives, decision, consequences, migration, and rollback considerations.
