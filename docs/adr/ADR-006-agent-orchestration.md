# ADR-006: Agent Orchestration

**Status:** Accepted  
**Decision date:** 2026-07-10

## Decision

Stateful multi-step agent flows with approval points use LangGraph. LangGraph is orchestration only; domain operations, parsers, repositories, and policies remain independently testable services.

## Mandatory patterns

Versioned state schema, structured outputs, interruptible human-in-the-loop points, run ID and trace, deterministic nodes where possible, and adapter-based model calls.

## Consequences

Simple deterministic pipelines do not require agents. Agents are used only where reasoning or multi-step state management is justified.
