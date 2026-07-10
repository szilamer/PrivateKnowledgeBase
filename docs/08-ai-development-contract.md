# AI Development Contract

**Version:** 0.3  
**Status:** Approved

## 1. Purpose

This contract defines how a code-generating or coding agent may modify the repository.

## 2. Document precedence

1. Accepted ADRs
2. Technical specification
3. System architecture
4. Domain model and ontology
5. Functional specification
6. MVP scope and product requirements
7. Project vision and concept

**Specification supplements** (when referenced by ADR, implementation plan, or this contract):

| Supplement | Scope |
|---|---|
| `docs/13-personal-source-connectors-supplement.md` | Declarative sources, host path bridging, Google connectors |
| `docs/14-source-connection-ui-supplement.md` | Source connection UI under `/sources` |

Supplements extend the documents above; they do not override accepted ADRs or the technical specification. When a supplement conflicts with a higher-precedence document, the higher-precedence document applies and the agent MUST report the conflict.

When documents conflict, the higher-precedence approved document applies. The agent MUST report the conflict.

## 3. Mandatory behavior

The agent MUST:

- cite the requirement or ADR implemented by each change;
- preserve module boundaries;
- use only approved technologies;
- produce small, reviewable changes;
- add or update tests;
- keep migrations reversible where feasible;
- validate structured AI outputs;
- apply authorization before data access;
- preserve provenance and audit data;
- update documentation when behavior changes.

### 3.1 Phase 7 — personal source connectors (mandatory when implementing Phase 7)

When implementing Phase 7, the agent MUST satisfy:

| Requirement | Source |
|---|---|
| Declarative `config/sources.yaml` with bootstrap upsert on API startup | FR-SRC-010, supplement §4 |
| Host paths (`~/Projects`) bridged to container paths without user-edited Docker mounts | FR-SRC-011, supplement §7.5 |
| `GET`/`PUT` `/api/v1/sources/config` with secrets redacted | supplement §8 |
| Extended `SourceType`: `google_drive`, `gmail`, `google_calendar` | supplement §6.1, ADR-013 |
| Google OAuth read-only scopes; tokens in `connector_credentials`, never in git or logs | FR-SRC-012, FR-SRC-017, ADR-013 |
| Unified sync-run status for all connector types | FR-SRC-016 |
| Source connection UI at `/sources` with Hungarian plain-language copy | supplement 14 |
| SSR uses `API_INTERNAL_URL`; browser uses `NEXT_PUBLIC_API_URL` | supplement 14 §9 |

### 3.2 Application settings — LLM and embeddings

When implementing user-facing settings, the agent MUST satisfy:

| Requirement | Source |
|---|---|
| Declarative `config/settings.yaml` for LLM base URL, models, embedding mode | ADR-007, Phase 7 pattern |
| `GET`/`PUT` `/api/v1/settings` with API keys redacted (env var reference only) | Secret handling policy |
| `GET` `/api/v1/settings/llm/health` for connectivity feedback | supplement 14 §4.2 |
| Settings UI at `/settings` with Hungarian plain-language copy | supplement 14 |
| Worker and API resolve effective LLM config from file + `.env` on each request/task | Runtime consistency |

API keys MUST remain in `.env` (`LLM_API_KEY` or `api_key_env`); never in `settings.yaml`.

Google connectors MAY be gated by `PKB_GOOGLE_CONNECTORS_ENABLED=false` when credentials are absent; local-folder bootstrap MUST work without Google.

## 4. Prohibited behavior

The agent MUST NOT:

- choose a substitute framework, database, queue, or agent library without an ADR;
- add production dependencies without justification and review;
- place secrets in code, examples, tests, logs, or prompts;
- bypass application services to write canonical data;
- perform direct Neo4j writes outside the projector;
- weaken tests to make a change pass;
- silently change public API contracts;
- implement external side effects not included in the approved scope;
- require users to edit `docker-compose.yml` or specify container-internal paths for local folders.

## 5. Handling open decisions

If implementation requires a decision not covered by an accepted ADR, the agent stops the affected implementation and creates an ADR proposal containing context, options, decision drivers, recommendation, consequences, and migration impact.

ADR-013 (`docs/adr/ADR-013-google-workspace-connectors.md`) governs Google connector design. While status is **Proposed**, Phase 7 Google work MUST follow it; acceptance is tracked separately.

## 6. Change package

Each generated change should include summary, linked requirements, design notes, changed files, tests, migrations, risks, rollback notes, and unresolved questions.

## 7. Completion checks

Before declaring completion, the agent verifies formatting, typing, tests, security checks, migration status, API compatibility, documentation, and absence of untracked generated artifacts.
