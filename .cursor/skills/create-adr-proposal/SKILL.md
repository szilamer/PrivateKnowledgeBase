---
name: create-adr-proposal
description: Create an Architecture Decision Record when implementation needs a technology or architecture decision not covered by accepted ADRs. Use before substituting any stack component.
---

# Create ADR Proposal

## When to use

- Adding a dependency not in the normative stack
- Changing database, queue, agent library, or deployment model
- Any decision blocked by `docs/08-ai-development-contract.md` §5

## Steps

1. Stop the affected implementation
2. Create `docs/adr/ADR-XXX-short-title.md` (next number after highest existing)
3. Use this structure:

```markdown
# ADR-XXX: Title

**Status:** Proposed
**Decision date:** YYYY-MM-DD

## Context
...

## Decision drivers
...

## Considered options
1. ...
2. ...

## Decision
...

## Consequences
...

## Migration and rollback
...
```

4. Do NOT implement until status is **Accepted**
5. When accepted, update `docs/12-technology-decisions-and-adr-index.md`

## Normative stack reference

See `docs/12-technology-decisions-and-adr-index.md` — do not deviate without ADR.
