---
name: add-langgraph-agent
description: Add a LangGraph agent flow with versioned state schema, tool contracts, and schema-validated outputs. Use for extraction, retrieval, answer synthesis, or entity resolution agents.
---

# Add LangGraph Agent

Per `docs/05-agent-architecture.md` and `docs/07-technical-specification.md` §7.

## Steps

1. **State schema** — versioned Pydantic model in `packages/agents/`
2. **Graph definition** — LangGraph with deterministic nodes where possible
3. **Tools** — invoke application services only; explicit tool contracts
4. **Prompt** — versioned template in `packages/prompts/`; record version in audit
5. **Output validation** — schema-validate all LLM outputs before any persistence
6. **Recording** — model, provider, prompt version, schema version, tokens, latency, run ID
7. **Human gates** — interruption points for approval-required operations
8. **Worker integration** — dispatch via `extraction` or appropriate queue
9. **Evaluation** — golden dataset test; compare to baseline on prompt/model changes

## Agent safety (MUST NOT)

- Write to Neo4j or canonical tables
- Access unauthorized sources
- Invent missing sources
- Expose secrets in prompts or logs

## Agents in MVP

Triage, Extraction, Entity Resolution, Retrieval Planner, Answer Synthesis — see `docs/05-agent-architecture.md` §2.
