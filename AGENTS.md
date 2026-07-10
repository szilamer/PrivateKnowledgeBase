# AI Development Guide

This repository implements the [AI Development Contract](docs/08-ai-development-contract.md).

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
```

## Module boundaries

- `packages/domain` MUST NOT import FastAPI, Celery, Neo4j drivers, provider SDKs, or UI code.
- FastAPI routes perform validation, authorization, and use-case invocation only.
- Neo4j writes are permitted only from the graph projection component.
- All LLM outputs must be schema-validated.

## Development commands

```bash
cp .env.example .env
make dev-setup   # local tooling
make up          # start full stack
make test        # run tests
make ci          # lint + typecheck + test
```

## Implementation phases

Follow `docs/11-implementation-plan-and-backlog.md`. Phase 0 (platform foundation) is scaffolded. Continue with Phase 1 (source registry and ingestion).
