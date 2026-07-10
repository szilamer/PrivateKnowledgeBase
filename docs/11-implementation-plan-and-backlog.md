# Implementation Plan and Backlog

**Version:** 0.1  
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

## 9. Initial epics

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

## 10. MVP exit criteria

All MVP requirements have passing acceptance tests, critical security findings are closed, recovery procedures are verified, the evaluation targets are met, and the technical documents reflect the implemented system.
