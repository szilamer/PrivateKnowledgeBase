# AI-Powered Personal Knowledge Operations System

Specification and implementation repository for a local-first, AI-powered personal knowledge operations system.

- **Documentation:** `docs/` — product, architecture, and ADRs
- **Implementation:** Phase 0 platform foundation (monorepo scaffold + Docker Compose)

## Quick start

Prerequisites: Docker Desktop, [uv](https://docs.astral.sh/uv/), Node.js 22+ (for local frontend work).

```bash
# 1. Configure environment
cp .env.example .env

# 2. Start the full stack (one command — ADR-001)
make up

# 3. Verify services
open http://localhost:3000    # Web UI
open http://localhost:8000/api/docs  # OpenAPI
curl http://localhost:8000/api/v1/health
```

Stop services: `make down`

## Development

```bash
make dev-setup   # install Python (uv) and Node dependencies locally
make test        # unit tests
make lint        # Ruff
make typecheck   # mypy
make ci          # full local quality gate
make migrate     # run Alembic migrations (when stack is up)
make logs        # tail container logs
```

## Repository layout

```text
apps/
  api/          FastAPI — /api/v1
  worker/       Celery — ingestion, extraction, embedding, graph_projection, maintenance
  web/          Next.js + TypeScript
packages/
  domain/       Framework-independent business types
  application/  Use cases
  adapters/     PostgreSQL, Redis, Neo4j integrations
  agents/       LangGraph flows (Phase 3+)
  ontology/     Version-controlled YAML definitions
  prompts/      Agent prompt templates
  observability/ Structured JSON logging
tests/
  unit/ integration/ contract/ e2e/
infra/docker/   Docker Compose (PostgreSQL+pgvector, Redis, Neo4j, API, worker, web)
docs/           Full specification package
```

## Technology stack (MVP)

| Area | Choice |
|---|---|
| Runtime | Docker Compose (local-first) |
| Backend | Python 3.12+, FastAPI, SQLAlchemy 2.x, Alembic |
| Data | PostgreSQL + pgvector, Neo4j Community, Redis |
| Jobs | Celery |
| Agents | LangGraph |
| Frontend | Next.js + TypeScript |

See [Technology Decisions and ADR Index](docs/12-technology-decisions-and-adr-index.md) for normative decisions.

## Recommended reading order

1. [Project Vision and Concept](docs/01-project-vision-and-concept.md)
2. [MVP Scope and Product Requirements](docs/02-mvp-scope-and-product-requirements.md)
3. [Functional Specification](docs/03-functional-specification.md)
4. [Domain Model and Ontology](docs/04-domain-model-and-ontology.md)
5. [Agent Architecture](docs/05-agent-architecture.md)
6. [System Architecture](docs/06-system-architecture.md)
7. [Technical Specification](docs/07-technical-specification.md)
8. [AI Development Contract](docs/08-ai-development-contract.md)
9. [Testing Strategy](docs/09-testing-strategy.md)
10. [Knowledge Management and Security Policy](docs/10-knowledge-management-and-security-policy.md)
11. [Implementation Plan and Backlog](docs/11-implementation-plan-and-backlog.md)
12. [Technology Decisions and ADR Index](docs/12-technology-decisions-and-adr-index.md)

## Implementation status

| Phase | Status |
|---|---|
| Phase 0 — Repository and infrastructure | Complete |
| Phase 1 — Source registry and ingestion | Complete |
| Phase 2 — Parsing and retrieval | Complete |
| Phase 3 — Knowledge proposals | Complete |
| Phase 4 — Canonical knowledge and graph | Complete |
| Phase 5 — Question answering and project overview | Complete |
| Phase 6 — Hardening | Complete |

Operator procedures: [Operator Guide](docs/operator-guide.md). Release gate: [Release Checklist](docs/release-checklist.md).

For AI-assisted development, see [AGENTS.md](AGENTS.md).

## Document statuses

- **Concept:** establishes direction and principles.
- **Draft:** detailed, but still contains decisions to be resolved.
- **Approved:** may be used as implementation input.
- **Implemented:** verified against the running system.
- **Obsolete:** no longer normative.

## Minimum conditions for code generation

Implementation may begin safely only when the MVP-relevant parts of documents 02–09 are approved and all affected architectural decisions are recorded as accepted ADRs.
