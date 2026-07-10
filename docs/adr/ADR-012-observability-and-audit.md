# ADR-012: Observability and Audit

**Status:** Accepted  
**Decision date:** 2026-07-10

## Decision

The system uses structured JSON logs and OpenTelemetry-compatible traces. Every processing and agent run receives a correlation ID. The append-only logical audit trail records actor or agent, objects read or modified, source/model/prompt/schema context, approvals, and result.

## Privacy rule

Full document content, prompts, and secrets are not logged by default. Diagnostic samples are masked and require explicit authorization.
