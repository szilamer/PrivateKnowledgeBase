# Agent Layer Implementation Plan

**Version:** 0.1  
**Status:** Draft  
**Related:** `docs/05-agent-architecture.md`, `docs/07-technical-specification.md` §7, ADR-006, `docs/08-ai-development-contract.md` §3.3

## 1. Purpose

This document bridges the normative agent architecture (`docs/05-agent-architecture.md`) and the as-built system. It defines:

- how agents consume the layered knowledge architecture;
- which agent roles are implemented today and how;
- a phased plan to bring remaining roles to spec compliance;
- acceptance criteria, file placement, and quality gates for each slice.

Agents and deterministic services share the same persistence model. Agents propose changes; application services persist, authorize, audit, and project.

## 2. Knowledge architecture (agent consumption model)

Agents MUST treat the following layers as the single source of operational truth:

| Layer | Primary store | Mutable by agents? | Agent read access |
|---|---|---|---|
| Source registry | PostgreSQL `sources`, `source_objects`, `source_object_versions` | No direct writes | Via application services only |
| Content derivatives | PostgreSQL `content_chunks` (+ pgvector) | No | Chunk text and embeddings for extraction and retrieval |
| Proposed knowledge | PostgreSQL `knowledge_proposals`, `extraction_runs` | Yes — create proposals only | List/filter via `ProposalRepository` |
| Canonical knowledge | PostgreSQL `canonical_*` | No — approval + materialization only | Read via `CanonicalRepository` |
| Graph read model | Neo4j | No — projector only | Read via `GraphRepository` |
| Audit | PostgreSQL `audit_events` | Append-only via `AuditWriter` | Correlation ID per run |

### 2.1 Processing lifecycle (incremental, not full re-run)

1. **Sync** registers or updates `source_object_versions` when `content_hash` changes.
2. **Extraction** (`extraction_status`: `pending` → `completed` | `failed` | `skipped`) produces chunks and embeddings once per version.
3. **Knowledge extraction** (`knowledge_status`: `pending` → `completed` | `failed` | `skipped`) produces `KnowledgeProposal` records once per version.
4. **Approval** (human or policy auto-approve) materializes canonical rows and outbox events.
5. **Graph projection** consumes outbox events into Neo4j.

Completed versions are not reprocessed unless a new version is created (content change) or an operator triggers explicit reprocessing (Maintenance Agent scope).

### 2.2 Agent safety boundary (normative)

Per ADR-006 and `docs/05-agent-architecture.md` §6:

- LangGraph nodes call **application services** and **ports**, not SQLAlchemy sessions or Neo4j drivers.
- Agents MUST NOT write to `canonical_*` or Neo4j.
- All LLM outputs MUST pass schema validation before proposal persistence.
- Every agent run records model, provider, prompt version, schema version, latency, and correlation ID.

## 3. Implementation status (as-built baseline)

**Baseline date:** 2026-07-10  
**Code references:** `packages/agents/`, `packages/application/`, `apps/worker/`, `apps/api/`

| Agent role (doc 05) | Implementation form | LangGraph? | Location | Maturity |
|---|---|---|---|---|
| Extraction | LangGraph flow + `KnowledgeExtractionService` | Yes | `packages/agents/extraction/`, `application/knowledge/extraction_service.py` | **Partial** — graph wired; LLM optional; heuristic fallback |
| Entity Resolution | Deterministic domain + proposal typing | No (embedded) | `domain/entity_resolution.py`, `extraction_service._persist_proposals` | **Partial** — no standalone graph or merge proposals |
| Retrieval Planner | `HybridRetrievalPlanner` service | No | `application/qa/answer_service.py` | **Partial** — no LangGraph; hybrid signals work |
| Answer Synthesis | `HeuristicAnswerSynthesizer` / `OpenAICompatibleAnswerSynthesizer` | No | `adapters/llm/answer_synthesis.py`, `application/qa/answer_service.py` | **Partial** — no LangGraph; citations present |
| Project Report | `StatusReportService`, `ProjectDashboardService` | No | `application/projects/` | **Stub** — static aggregation, not agent-driven |
| Maintenance | Pipeline recovery, rebuild projection | No | `worker/recovery.py`, `application/operations/` | **Partial** — no stale/orphan detection agent |
| Triage | — | No | — | **Not started** |
| Contradiction | Domain types only | No | `domain/` (contradiction model) | **Not started** |
| Ontology Curator | — | No | — | **Not started** |

### 3.1 Supporting infrastructure (complete)

The following are **not agents** but required foundations already in place:

- Celery pipeline with re-chaining: `ingestion` → `extraction` → `knowledge_extraction` → `graph_projection`
- Worker startup recovery: `apps/worker/src/worker/recovery.py`
- Resilient embeddings (API with hash fallback): `adapters/embeddings/resilient.py`
- Proposal approval and auto-approve (≥ 0.8 confidence entities): `application/knowledge/proposal_service.py`
- Settings UI and runtime LLM resolution: `config/settings.yaml`, `/api/v1/settings`

## 4. Target architecture

```text
packages/agents/
  extraction/     # Phase A — extend existing graph
  triage/         # Phase B
  resolution/     # Phase C — optional graph around existing logic
  contradiction/  # Phase D
  ontology/       # Phase E
  retrieval/      # Phase F — wrap HybridRetrievalPlanner
  synthesis/      # Phase G — wrap answer synthesizers
  report/         # Phase H
  maintenance/    # Phase I

packages/application/   # use cases, ports (unchanged boundary)
packages/prompts/       # versioned prompt templates per agent
apps/worker/            # Celery dispatch per queue
apps/api/               # synchronous agent endpoints where user-facing
```

Each new LangGraph flow MUST have:

1. Versioned state schema (`packages/agents/<name>/state.py`)
2. Compiled graph (`packages/agents/<name>/graph.py`)
3. Application runner that wires tools (`packages/application/` or thin worker adapter)
4. Prompt template (`packages/prompts/<name>_vN.py`)
5. Unit tests (golden inputs) + integration test where LLM is mocked
6. Audit + run metadata persistence

## 5. Delivery phases

Phases are vertical slices. Each slice links requirement IDs, updates `docs/05-agent-architecture.md` status, and passes `make ci`.

### Phase A — Extraction Agent hardening (EPIC-04 extension)

**Goal:** Make the Extraction Agent production-complete per doc 05 and ADR-006.

| ID | Work item | Acceptance |
|---|---|---|
| A-1 | Split `extract` node: LLM path vs heuristic path explicit in graph | Graph state records `provider` and `fallback_used` |
| A-2 | Schema validation gate node before `persist` | Invalid LLM JSON → failed run + audit, no orphan proposals |
| A-3 | Record token usage on `extraction_runs` | `token_usage` populated when LLM used |
| A-4 | Interrupt point after extraction for `requires_review` batch | Graph supports `interrupt` metadata; worker continues async approval path |
| A-5 | Golden dataset: 5 fixture documents | `tests/unit` or `tests/contract` assert entity/task counts within tolerance |
| A-6 | Operator visibility: extraction errors on failed versions | `extraction_error` column surfaced in API/UI |

**Queues:** `extraction`  
**Requirements:** FR-EXT-001..004 (functional spec), ADR-006, ADR-007

---

### Phase B — Triage Agent (EPIC-13)

**Goal:** Classify new `source_object_versions` before extraction priority and project assignment.

| ID | Work item | Acceptance |
|---|---|---|
| B-1 | State schema: `version_id`, `project_hint`, `sensitivity`, `relevance`, `extractor_hint`, `review_risk` | Pydantic-validated state |
| B-2 | LangGraph: `load_metadata` → `classify` → `persist_hints` | Classification stored on version metadata JSON or dedicated columns |
| B-3 | Worker hook: run triage on new pending versions before extraction ordering | `.md`/`.txt` still prioritized; triage adjusts batch order |
| B-4 | UI: show triage labels on source object detail | Hungarian labels in web UI |
| B-5 | Policy: high-sensitivity objects flag `requires_review` on downstream proposals | Proposal `risk_level` elevated |

**Queues:** new `triage` queue or pre-step in `extraction`  
**Migration:** optional `triage_status`, `triage_metadata JSONB` on `source_object_versions`  
**Requirements:** New FR-TRI-001..003 (to be added to functional spec §3.1)

---

### Phase C — Entity Resolution Agent (EPIC-04 extension)

**Goal:** Promote embedded resolution logic to an explicit agent with merge/link/ambiguous flows.

| ID | Work item | Acceptance |
|---|---|---|
| C-1 | LangGraph wrapping `resolve_entity` + candidate retrieval tool | `ENTITY_RESOLUTION` proposals include ranked candidates |
| C-2 | Merge proposal type with destructive gate | Merge requires human approval; cannot auto-approve |
| C-3 | Alias table or `entity_index` alias column | Approved alias persists and improves future matching |
| C-4 | Golden tests: exact match, alias match, ambiguous pair | Regression suite in `tests/unit/test_entity_resolution.py` extended |

**Note:** Per ADR-006, deterministic scoring may remain a graph node; LLM is optional for borderline cases only.

---

### Phase D — Contradiction Agent (EPIC-06 extension)

**Goal:** Compare new claims against active canonical claims; surface findings.

| ID | Work item | Acceptance |
|---|---|---|
| D-1 | LangGraph: `load_candidate_claims` → `compare` → `persist_findings` | `contradiction_findings` rows created with evidence |
| D-2 | Trigger: after claim materialization (outbox consumer side effect or maintenance batch) | New claim checked within same pipeline generation |
| D-3 | UI: contradictions view in graph or proposals | User can see conflicting predicates and sources |
| D-4 | No auto-merge or auto-reject | Findings are informational; resolution is human |

**Requirements:** FR-CLM-001..002, graph contradiction view (Phase 4 backlog)

---

### Phase E — Ontology Curator Agent (EPIC-14 new)

**Goal:** Detect unmapped recurring concepts; create `OntologyProposal` records (not YAML writes).

| ID | Work item | Acceptance |
|---|---|---|
| E-1 | Aggregate unmapped entity strings from proposals | Weekly or on-demand Celery task |
| E-2 | LangGraph proposes entity type / relationship additions | Output is `ontology_proposals` table row |
| E-3 | Human approval required for all ontology changes | Aligns with doc 05 §4 |
| E-4 | Read-only access to `packages/ontology/*.yaml` | Agent reads; never writes normative YAML |

**Migration:** `ontology_proposals` if not present  
**API:** `/api/v1/ontology-proposals` (listed in technical spec §3)

---

### Phase F — Retrieval Planner Agent (EPIC-07 extension)

**Goal:** Promote `HybridRetrievalPlanner` to a versioned LangGraph for complex questions.

| ID | Work item | Acceptance |
|---|---|---|
| F-1 | State schema: question, plan steps, retrieved citation IDs | Matches `RetrievalPlanStep` domain type |
| F-2 | Graph nodes map 1:1 to existing search/canonical/graph tools | No direct DB access |
| F-3 | `QuestionAnsweringService` invokes graph when `mode=hybrid` and planner v2 enabled | Feature flag in settings |
| F-4 | Log plan in audit for `/questions` responses | `correlation_id` links answer to plan |

**Note:** Simple keyword/semantic modes may keep the deterministic planner (ADR-006).

---

### Phase G — Answer Synthesis Agent (EPIC-08 extension)

**Goal:** LLM synthesis with explicit uncertainty and conflict reporting.

| ID | Work item | Acceptance |
|---|---|---|
| G-1 | LangGraph: `build_context` → `synthesize` → `validate_citations` | Answer cites only retrieved citation IDs |
| G-2 | Output schema: `answer`, `confidence`, `warnings`, `conflicts` | Zod/Pydantic validated |
| G-3 | Hallucination guard: citation IDs must exist in context package | Test rejects invented chunk IDs |
| G-4 | Hungarian UI displays warnings | `/questions` or chat UI |

---

### Phase H — Project Report Agent (EPIC-09 extension)

**Goal:** Time-bounded narrative reports from canonical + graph data.

| ID | Work item | Acceptance |
|---|---|---|
| H-1 | LangGraph: `load_project_subgraph` → `summarize_changes` → `format_report` | Markdown report with sections: changes, risks, decisions, open tasks |
| H-2 | API: `POST /api/v1/projects/{id}/reports` async job | Celery `maintenance` or new `report` queue |
| H-3 | Report stored as `source_object` or downloadable artifact | Provenance links to canonical IDs |
| H-4 | Evaluation: golden project fixture | Report contains expected decision/task references |

---

### Phase I — Maintenance Agent (EPIC-10 extension)

**Goal:** Proactive health of embeddings, projections, and orphaned records.

| ID | Work item | Acceptance |
|---|---|---|
| I-1 | Scheduled Celery beat or startup + periodic task | Configurable interval in settings |
| I-2 | Checks: pending queue depth, failed extraction count, outbox lag, embedding model drift | `OperationsStatusService` extended |
| I-3 | Actions: re-enqueue stalled pipelines, flag versions with model mismatch | No silent data deletion |
| I-4 | Operator UI on `/operations` | Hungarian status copy |

---

## 6. Priority order (recommended)

```text
A (Extraction hardening) → C (Entity Resolution) → D (Contradiction)
    → F (Retrieval Planner) → G (Answer Synthesis)
    → B (Triage) → H (Project Report) → E (Ontology) → I (Maintenance)
```

**Rationale:**

1. **A, C** improve knowledge quality entering the canonical layer.
2. **D** depends on canonical claims existing.
3. **F, G** improve user-facing Q&A (highest visible value after extraction).
4. **B** optimizes ingestion order once extraction is stable.
5. **H, E, I** are operational and governance enhancements.

## 7. Epics and backlog mapping

Add to `docs/11-implementation-plan-and-backlog.md`:

| Epic | Phases | Description |
|---|---|---|
| EPIC-04 | A, C | Knowledge extraction and entity resolution agents |
| EPIC-06 | D | Contradiction detection agent |
| EPIC-07 | F | Retrieval planner agent |
| EPIC-08 | G | Answer synthesis agent |
| EPIC-09 | H | Project report agent |
| EPIC-10 | I | Maintenance agent |
| EPIC-13 | B | Triage agent |
| EPIC-14 | E | Ontology curator agent |

## 8. Testing and evaluation

Per `docs/05-agent-architecture.md` §7 and `docs/09-testing-strategy.md`:

| Test type | Applies to |
|---|---|
| Schema validity | All LLM-producing agents (A, B, C, D, E, F, G, H) |
| Golden dataset regression | A, C, F, G, H |
| Provenance / citation integrity | G, H |
| Authorization | All agents reading owner-scoped data |
| Hallucination / invented source | G (mandatory), H |
| Graph safety | All — no direct Neo4j writes in agent code |

Contract tests MUST mock LLM adapters; CI MUST NOT require live API keys.

## 9. Configuration

| Setting | Purpose | Location |
|---|---|---|
| `llm.enabled` | Master LLM switch | `config/settings.yaml` |
| `embedding.provider` | `hash` \| `api` \| `auto` | `config/settings.yaml` |
| `agents.extraction.use_langgraph` | Feature flag (default true) | `config/settings.yaml` (new) |
| `agents.triage.enabled` | Phase B gate | `config/settings.yaml` (new) |
| `agents.planner.version` | `deterministic` \| `graph_v2` | `config/settings.yaml` (new) |

Worker and API MUST resolve effective config on each task/request (same pattern as LLM settings).

## 10. Documentation updates (this initiative)

When implementing each phase, the coding agent MUST update:

| Document | Update |
|---|---|
| `docs/05-agent-architecture.md` | §8 status matrix row |
| `docs/11-implementation-plan-and-backlog.md` | Phase 8 checklist items |
| `docs/07-technical-specification.md` | §7 agent inventory |
| `docs/08-ai-development-contract.md` | §3.3 if new mandatory rules emerge |
| `README.md` | Implementation status table |

## 11. MVP exit criteria (agent layer)

Agent layer MVP is complete when:

1. Phases **A, C, F, G** are **Implemented** in doc 05 §8.
2. All agent graphs pass schema validation tests without live LLM.
3. Q&A path demonstrates citation-backed answers from persisted knowledge.
4. No agent writes directly to canonical tables or Neo4j (verified by code review / lint rules).
5. Operator can see extraction/knowledge errors and pipeline progress in UI.
6. `docs/05-agent-architecture.md` status is **Approved** (no longer Draft).

Phases B, D, E, H, I may ship incrementally after MVP agent exit if product priority allows; they MUST be tracked as **Planned** in doc 05 §8.

## 12. Open decisions

| ID | Question | Recommendation |
|---|---|---|
| OD-1 | Separate `triage` Celery queue vs inline pre-extraction step? | Inline pre-step in Phase B; extract queue if load warrants |
| OD-2 | Entity Resolution LLM for ambiguous cases? | Deterministic first; optional LLM node behind feature flag |
| OD-3 | Contradiction trigger: synchronous or batch? | Batch on materialization + nightly sweep |
| OD-4 | ADR for ontology proposal schema? | Create ADR-014 when Phase E starts |

Unresolved OD items MUST NOT block Phase A implementation.
