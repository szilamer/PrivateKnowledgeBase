# Agent Architecture

**Version:** 0.2  
**Status:** Draft

## 1. Principles

Agents are controlled decision components, not unrestricted autonomous processes. Deterministic parsing, validation, persistence, authorization, and projection remain ordinary services. Agents use tools through explicit interfaces and return structured outputs.

**Implementation plan:** `docs/15-agent-implementation-plan.md` defines phased delivery, as-built status, and acceptance criteria for each role below.

## 2. Agent roles

### Triage Agent
Classifies source objects by project, sensitivity, relevance, expected extractor, and review risk.

**Implementation:** Planned (Phase B). See doc 15.

### Extraction Agent
Produces entities, claims, tasks, decisions, events, and evidence mappings according to a versioned schema.

**Implementation:** Partial — LangGraph flow (`packages/agents/extraction/`) wired via `KnowledgeExtractionService`; LLM optional with heuristic fallback.

### Entity Resolution Agent
Suggests matches, aliases, merges, or new entities. Ambiguous merges require approval.

**Implementation:** Partial — deterministic `resolve_entity` embedded in extraction persist path; standalone LangGraph planned (Phase C).

### Contradiction Agent
Compares new claims with active claims and creates findings with supporting evidence.

**Implementation:** Not started (Phase D). Domain model exists; no agent graph.

### Ontology Curator Agent
Detects recurring unmapped concepts and creates ontology proposals. It cannot alter normative YAML.

**Implementation:** Not started (Phase E).

### Retrieval Planner
Transforms a user question into authorized keyword, vector, and graph retrieval steps.

**Implementation:** Partial — `HybridRetrievalPlanner` service (deterministic); LangGraph promotion planned (Phase F).

### Answer Synthesis Agent
Produces an evidence-backed answer from the approved context package. It must identify uncertainty and conflicting sources.

**Implementation:** Partial — `HeuristicAnswerSynthesizer` / `OpenAICompatibleAnswerSynthesizer`; LangGraph promotion planned (Phase G).

### Project Report Agent
Generates time-bounded project summaries, changes, risks, decisions, and open tasks.

**Implementation:** Stub — `StatusReportService` / `ProjectDashboardService`; agent graph planned (Phase H).

### Maintenance Agent
Identifies stale embeddings, projection lag, orphaned records, and reprocessing needs.

**Implementation:** Partial — pipeline recovery and projection rebuild; proactive detection agent planned (Phase I).

## 3. Orchestration

Stateful, multi-step flows use LangGraph. Each graph has a versioned state schema, deterministic nodes where possible, explicit tool contracts, interruption points, retry rules, and a run identifier.

Simple deterministic pipelines do not require an agent graph.

## 4. Human-in-the-loop gates

Mandatory review applies to ontology changes, destructive merges, high-impact decisions, low-confidence claims, access-policy changes, and external side effects.

## 5. Agent output contract

Each output includes schema version, run ID, source references, proposed operations, confidence, assumptions, warnings, and required approval level.

## 6. Safety and limits

Agents MUST NOT:

- access a source outside the caller's authorization;
- write directly to Neo4j or canonical tables;
- invent missing sources;
- expose secrets in prompts or logs;
- modify external systems in the MVP;
- add a dependency or technology contrary to an accepted ADR.

## 7. Evaluation

Each agent has golden datasets, schema-validity tests, provenance checks, hallucination tests, and regression metrics. Model replacement requires evaluation against the same baseline.

## 8. Implementation status matrix

Normative roles map to delivery phases in `docs/15-agent-implementation-plan.md`.

| Agent role | Form | LangGraph | Phase | Status |
|---|---|---|---|---|
| Extraction | Graph + service | Yes | A | Partial |
| Entity Resolution | Graph + domain scoring | Yes | C | Implemented |
| Retrieval Planner | Graph + service | Yes | F | Implemented |
| Answer Synthesis | Graph + adapters | Yes | G | Implemented |
| Project Report | Service | No (planned H) | H | Stub |
| Maintenance | Recovery ops | No (planned I) | I | Partial |
| Triage | — | Planned | B | Not started |
| Contradiction | Graph + domain compare | Yes | D | Implemented |
| Ontology Curator | — | Planned | E | Not started |

**Status values:** Not started | Stub | Partial | Implemented

An agent is **Implemented** only when its phase acceptance criteria in doc 15 are met and tests pass in CI without live LLM keys.
