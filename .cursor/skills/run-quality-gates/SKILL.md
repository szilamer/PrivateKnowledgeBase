---
name: run-quality-gates
description: Run full quality gates before declaring work complete. Use before commits, PRs, or when the user asks if implementation is done.
---

# Run Quality Gates

Per `docs/08-ai-development-contract.md` §7 and `docs/07-technical-specification.md` §9.

## Checklist

```bash
make ci    # ruff lint + format check + mypy + pytest
```

Additional checks when applicable:

- [ ] Alembic: `upgrade head` and `downgrade -1` succeed
- [ ] OpenAPI at `/api/docs` reflects API changes
- [ ] No secrets in diff (`.env`, tokens, keys)
- [ ] Requirement ID cited (MVP-XX / EPIC-XX)
- [ ] ADR referenced for architectural decisions
- [ ] Tests added for new behavior — not weakened
- [ ] Authorization and audit implemented for mutating operations
- [ ] Migrations included and reversible
- [ ] No untracked generated artifacts committed

## Definition of done

A feature is complete only when:

- Requirement ID linked
- Tests pass
- Authorization and audit behavior implemented
- Failure modes documented
- Migrations included
- Relevant docs updated

## If CI fails

Fix issues autonomously. Do not weaken tests to pass.
