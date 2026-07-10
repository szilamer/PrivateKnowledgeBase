# ADR-007: LLM and Embedding Strategy

**Status:** Accepted  
**Decision date:** 2026-07-10

## Decision

The system uses provider-independent `LLMProvider` and `EmbeddingProvider` interfaces. The MVP supports at least one OpenAI-compatible cloud provider and one OpenAI-compatible local endpoint. Models are configurable by purpose: extraction, classification, synthesis, and embedding. Vendor SDKs are not used in domain or use-case layers.

## Privacy rule

A policy decision determines whether content may leave the local environment. If prohibited, an approved local provider must be used or the operation is blocked.

## Consequences

Prompts are versioned files. Model, prompt, and schema versions are audited. Provider replacement does not alter the domain model.
