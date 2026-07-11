---
name: add-langgraph-agent
description: Add a LangGraph agent flow with versioned state schema, tool contracts, and schema-validated outputs. Use for extraction, retrieval, answer synthesis, or entity resolution agents.
---

# Add LangGraph Agent

Per `docs/05-agent-architecture.md`, `docs/15-agent-implementation-plan.md`, and `docs/07-technical-specification.md` §7.

Before starting, identify the delivery phase (A–I) in doc 15 and confirm acceptance criteria for that phase.

## Steps

1. **State schema** — versioned Pydantic model in `packages/agents/<name>/state.py`
2. **Graph definition** — LangGraph with deterministic nodes where possible
3. **Tools** — invoke application services only; explicit tool contracts
4. **Prompt** — versioned template in `packages/prompts/<name>_vN.py`; record version in audit
5. **Output validation** — schema-validate all LLM outputs before any persistence
6. **Recording** — model, provider, prompt version, schema version, tokens, latency, run ID
7. **Human gates** — interruption points for approval-required operations
8. **Worker integration** — dispatch via appropriate Celery queue (see doc 15 §5)
9. **Evaluation** — golden dataset test; compare to baseline on prompt/model changes
10. **Documentation** — update doc 05 §8 status matrix and doc 11 Phase 8 checklist

## Agent safety (MUST NOT)

- Write to Neo4j or canonical tables
- Access unauthorized sources
- Invent missing sources
- Expose secrets in prompts or logs

## Agents in MVP

Priority order and phase mapping: `docs/15-agent-implementation-plan.md` §6.

MVP agent exit requires Phases A, C, F, G (Extraction, Entity Resolution, Retrieval Planner, Answer Synthesis).

## Dev contract

Mandatory rules: `docs/08-ai-development-contract.md` §3.3.
