# Implementation Plan and Backlog

**Version:** 0.2  
**Status:** Draft

## 1. Delivery approach

Implementation proceeds in vertical slices. Each slice must produce observable user value and include domain logic, API, persistence, authorization, audit, tests, and minimal UI.

## 2. Phase 0 — Repository and infrastructure

- establish repository layout;
- Docker Compose services;
- CI quality gates;
- configuration and secret handling;
- health checks, logging, tracing;
- PostgreSQL migrations and outbox foundation.

## 3. Phase 1 — Source registry and ingestion

- local-folder source registration;
- GitHub repository registration;
- synchronization runs;
- source object identity and immutable versions;
- content hashing, incremental detection, retries, and error UI.

## 4. Phase 2 — Parsing and retrieval foundation

- Markdown, text, and PDF parsers;
- chunking and embeddings;
- pgvector search;
- source preview and citation anchors;
- retrieval authorization filters.

## 5. Phase 3 — Knowledge proposals

- extraction schemas;
- LangGraph extraction flow;
- entity resolution;
- proposal store and approval queue;
- provenance and audit.

## 6. Phase 4 — Canonical knowledge and graph

- canonical entities and claims;
- outbox projector;
- Neo4j schema and indexes;
- graph browser;
- temporal and contradiction views.

## 7. Phase 5 — Question answering and project overview

- hybrid retrieval planner;
- answer synthesis with citations;
- project dashboard;
- time-bounded status reports;
- evaluation suite and quality thresholds.

## 8. Phase 6 — Hardening

- backup/restore;
- projection rebuild;
- load and security testing;
- documentation review;
- release checklist and operator guide.

## 9. Phase 7 — Personal sources and connection UI

Specification supplements:

- `docs/13-personal-source-connectors-supplement.md`
- `docs/14-source-connection-ui-supplement.md`
- `docs/adr/ADR-013-google-workspace-connectors.md` (proposed)

Delivery slices:

- **7a** — declarative `config/sources.yaml`, host path bridge, bootstrap sync (no manual Docker mounts)
- **7b** — Google OAuth foundation and credential storage
- **7c** — Google Drive folder connector
- **7d** — Gmail connector
- **7e** — Google Calendar connector
- **7f** — Source Connection UI (`/sources`, `/sources/connect/*` wizards, Hungarian copy)
- **7g** — acceptance tests AT-SRC-01 … AT-SRC-05 and UX criteria from doc 14

## 10. Phase 8 — Agent layer completion

Specification:

- `docs/05-agent-architecture.md` — normative roles and safety rules
- `docs/15-agent-implementation-plan.md` — phased delivery and acceptance criteria

Delivery phases (see doc 15 §5 for full work items):

- **8a / Phase A** — Extraction Agent hardening (schema gate, token usage, golden tests)
- **8b / Phase C** — Entity Resolution Agent (explicit graph, merge gates)
- **8c / Phase F** — Retrieval Planner Agent (LangGraph for hybrid mode)
- **8d / Phase G** — Answer Synthesis Agent (citation validation, uncertainty output)
- **8e / Phase D** — Contradiction Agent
- **8f / Phase B** — Triage Agent
- **8g / Phase H** — Project Report Agent
- **8h / Phase E** — Ontology Curator Agent
- **8i / Phase I** — Maintenance Agent

**MVP agent exit** (doc 15 §11): phases 8a, 8b, 8c, 8d complete; doc 05 §8 rows marked **Implemented** for Extraction, Entity Resolution, Retrieval Planner, and Answer Synthesis.

## 11. Initial epics

- EPIC-01 Platform foundation
- EPIC-02 Source connectors
- EPIC-03 Document processing
- EPIC-04 Knowledge extraction
- EPIC-05 Approval workflow
- EPIC-06 Knowledge graph
- EPIC-07 Hybrid retrieval
- EPIC-08 Question answering
- EPIC-09 Project intelligence
- EPIC-10 Security and operations
- EPIC-11 Personal source connectors (Phase 7)
- EPIC-12 Source connection UI (Phase 7)
- EPIC-13 Triage agent (Phase 8b)
- EPIC-14 Ontology curator agent (Phase 8h)

## 12. MVP exit criteria

All MVP requirements have passing acceptance tests, critical security findings are closed, recovery procedures are verified, the evaluation targets are met, the technical documents reflect the implemented system, and agent layer MVP exit criteria in `docs/15-agent-implementation-plan.md` §11 are satisfied.
