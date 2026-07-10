# AI Development Contract

**Version:** 0.2  
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

## 4. Prohibited behavior

The agent MUST NOT:

- choose a substitute framework, database, queue, or agent library without an ADR;
- add production dependencies without justification and review;
- place secrets in code, examples, tests, logs, or prompts;
- bypass application services to write canonical data;
- perform direct Neo4j writes outside the projector;
- weaken tests to make a change pass;
- silently change public API contracts;
- implement external side effects not included in the approved scope.

## 5. Handling open decisions

If implementation requires a decision not covered by an accepted ADR, the agent stops the affected implementation and creates an ADR proposal containing context, options, decision drivers, recommendation, consequences, and migration impact.

## 6. Change package

Each generated change should include summary, linked requirements, design notes, changed files, tests, migrations, risks, rollback notes, and unresolved questions.

## 7. Completion checks

Before declaring completion, the agent verifies formatting, typing, tests, security checks, migration status, API compatibility, documentation, and absence of untracked generated artifacts.
