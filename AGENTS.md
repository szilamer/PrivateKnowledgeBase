# AI Development Guide

This repository implements the [AI Development Contract](docs/08-ai-development-contract.md).

Cursor-specific configuration lives in `.cursor/rules/`, `.cursor/skills/`, and `.cursor/hooks.json`.

## Current phase

**Phase 3 — Knowledge proposals** (Phase 1–2 complete)

Phase 1 (MVP-01, MVP-02) and Phase 2 (parsers, chunking, embeddings, search) are implemented. Current work: extraction schemas, LangGraph flow, entity resolution, proposal store, approval queue.

## Document precedence

1. Accepted ADRs in `docs/adr/`
2. Technical specification (`docs/07-technical-specification.md`)
3. System architecture (`docs/06-system-architecture.md`)
4. Domain model (`docs/04-domain-model-and-ontology.md`)
5. Functional specification (`docs/03-functional-specification.md`)
6. MVP scope (`docs/02-mvp-scope-and-product-requirements.md`)
7. Project vision (`docs/01-project-vision-and-concept.md`)

## Repository layout

```text
apps/api/       FastAPI REST service
apps/worker/    Celery background workers
apps/web/       Next.js frontend
packages/       Domain, application, adapters, agents, ontology, prompts, observability
tests/          unit, integration, contract, e2e
infra/docker/   Docker Compose stack
docs/           Product and architecture documentation
.cursor/        Cursor rules, skills, hooks
```

## Module boundaries

- `packages/domain` MUST NOT import FastAPI, Celery, Neo4j drivers, provider SDKs, or UI code.
- FastAPI routes perform validation, authorization checks, and use-case invocation only.
- Neo4j writes are permitted only from the graph projection component.
- All LLM outputs must be schema-validated.
- LangGraph tools invoke application services — not database clients.

## Development commands

```bash
cp .env.example .env
make dev-setup   # local tooling
make up          # start full stack
make test        # run tests
make ci          # lint + typecheck + test
make migrate     # Alembic migrations (stack running)
```

## Cursor skills (project)

| Skill | Use when |
|---|---|
| `implement-vertical-slice` | Starting any new feature or MVP requirement |
| `phase-1-source-ingestion` | MVP-01, MVP-02, source connectors |
| `add-api-endpoint` | New REST resource under `/api/v1` |
| `add-celery-task` | Background job in ingestion/extraction/embedding/graph_projection/maintenance |
| `add-alembic-migration` | PostgreSQL schema change |
| `add-langgraph-agent` | Extraction, retrieval, or synthesis agent |
| `neo4j-projection-only` | Graph reads or projection writes |
| `create-adr-proposal` | Technology decision not covered by ADRs |
| `run-quality-gates` | Before declaring work complete |

## Change package template

Every significant change should include:

```
## Summary
[MVP-XX / EPIC-XX] Brief description

## Requirements & ADRs
- MVP-XX: ...
- ADR-00X: ...

## Design notes
...

## Tests
- unit: ...
- integration: ...

## Migrations
- 000X_name (reversible: yes/no)

## Risks / rollback
...

## Open questions
...
```

## Definition of done

- [ ] Requirement ID linked
- [ ] Tests pass (`make ci`)
- [ ] Authorization and audit for mutating operations
- [ ] Failure modes documented
- [ ] Migrations included and reversible
- [ ] Docs updated when behavior changes
- [ ] No secrets in code or commits

## Prohibited patterns

- Substituting stack components without ADR
- Direct Neo4j writes outside projector
- Bypassing application services for canonical data
- Weakening tests to pass
- Secrets in code, logs, or prompts

## Implementation phases

| Phase | Status |
|---|---|
| Phase 0 — Repository and infrastructure | Done (scaffolded) |
| Phase 1 — Source registry and ingestion | Done |
| Phase 2 — Parsing and retrieval | Done |
| Phase 3 — Knowledge proposals | **Current** |
| Phase 4 — Canonical knowledge and graph | Not started |
| Phase 5 — Q&A and project overview | Not started |
| Phase 6 — Hardening | Not started |

See `docs/11-implementation-plan-and-backlog.md` for full backlog.
