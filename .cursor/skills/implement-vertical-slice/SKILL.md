---
name: implement-vertical-slice
description: Implement a feature as an end-to-end vertical slice per docs/11. Use when implementing MVP requirements, epics, or Phase work across domain, API, worker, and UI.
---

# Implement Vertical Slice

## When to use

Starting any new feature, MVP requirement (MVP-01–MVP-07), or epic (EPIC-01–EPIC-10).

## Workflow

1. **Read specs** — identify requirement ID, read relevant ADRs and `docs/04-domain-model-and-ontology.md`
2. **Domain** — types, validation, lifecycle in `packages/domain`
3. **Application** — use case in `packages/application` with authorization + audit
4. **Adapters** — repository implementation in `packages/adapters`
5. **API or worker** — route or Celery task calling the use case only
6. **Migration** — Alembic if schema changes (reversible)
7. **Tests** — unit for domain; integration for adapters
8. **UI** — minimal surface in `apps/web` if user-visible
9. **Verify** — `make ci`
10. **Document** — change package with requirement ID, ADR refs, rollback notes

## Change package template

```
## Summary
[MVP-XX / EPIC-XX] Brief description

## Requirements
- MVP-XX: ...

## ADRs
- ADR-00X: ...

## Design notes
...

## Tests
- [ ] unit: ...
- [ ] integration: ...

## Migrations
- [ ] 000X_description (reversible)

## Risks / open questions
...
```

## Stop conditions

- Missing ADR for a technology decision → create ADR proposal first
- Document conflict → report and ask before proceeding
