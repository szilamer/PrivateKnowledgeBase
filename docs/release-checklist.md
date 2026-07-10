# Release Checklist

**Version:** 0.1  
**Scope:** MVP Phase 0–6

## Pre-release

- [ ] `.env` uses non-default secrets for PostgreSQL, Neo4j, and API keys
- [ ] `make ci` passes locally
- [ ] GitHub Actions CI green on `main`
- [ ] `make up && make migrate` succeeds on a clean machine
- [ ] `curl http://localhost:8000/api/v1/health` returns healthy
- [ ] `curl http://localhost:8000/api/v1/operations/status` returns expected counts

## Functional smoke

- [ ] Register a local-folder source and run sync
- [ ] Search returns chunked results with citations
- [ ] Approve a knowledge proposal
- [ ] Graph browser shows projected entities
- [ ] Ask a question on `/ask` returns cited answer
- [ ] Project dashboard loads on `/projects`

## Operations

- [ ] `make backup` produces `postgres.sql`
- [ ] `make restore BACKUP=<dir>` restores data
- [ ] `make rebuild-projection` repopulates Neo4j
- [ ] `make load-smoke` passes (50 health checks)

## Documentation

- [ ] README implementation status reflects Phases 0–6
- [ ] AGENTS.md current phase updated
- [ ] Operator guide reviewed (`docs/operator-guide.md`)

## Known MVP limitations

- Single-user local policy stub (no OAuth)
- No automated Neo4j backup (rebuild from PostgreSQL instead)
- Evaluation suite is unit-level; no full e2e pipeline test in CI

## Sign-off

| Role | Name | Date |
|---|---|---|
| Operator | | |
| Developer | | |
