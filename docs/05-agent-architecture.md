# Agent Architecture

**Version:** 0.1  
**Status:** Draft

## 1. Principles

Agents are controlled decision components, not unrestricted autonomous processes. Deterministic parsing, validation, persistence, authorization, and projection remain ordinary services. Agents use tools through explicit interfaces and return structured outputs.

## 2. Agent roles

### Triage Agent
Classifies source objects by project, sensitivity, relevance, expected extractor, and review risk.

### Extraction Agent
Produces entities, claims, tasks, decisions, events, and evidence mappings according to a versioned schema.

### Entity Resolution Agent
Suggests matches, aliases, merges, or new entities. Ambiguous merges require approval.

### Contradiction Agent
Compares new claims with active claims and creates findings with supporting evidence.

### Ontology Curator Agent
Detects recurring unmapped concepts and creates ontology proposals. It cannot alter normative YAML.

### Retrieval Planner
Transforms a user question into authorized keyword, vector, and graph retrieval steps.

### Answer Synthesis Agent
Produces an evidence-backed answer from the approved context package. It must identify uncertainty and conflicting sources.

### Project Report Agent
Generates time-bounded project summaries, changes, risks, decisions, and open tasks.

### Maintenance Agent
Identifies stale embeddings, projection lag, orphaned records, and reprocessing needs.

## 3. Orchestration

Stateful, multi-step flows use LangGraph. Each graph has a versioned state schema, deterministic nodes where possible, explicit tool contracts, interruption points, retry rules, and a run identifier.

Simple deterministic pipelines do not require an agent graph.

## 4. Human-in-the-loop gates

Mandatory review applies to ontology changes, destructive merges, high-impact decisions, low-confidence claims, access-policy changes, and external side effects.

## 5. Agent output contract

Each output includes schema version, run ID, source references, proposed operations, confidence, assumptions, warnings, and required approval level.

## 6. Safety and limits

Agents MUST NOT:

- access a source outside the caller's authorization;
- write directly to Neo4j or canonical tables;
- invent missing sources;
- expose secrets in prompts or logs;
- modify external systems in the MVP;
- add a dependency or technology contrary to an accepted ADR.

## 7. Evaluation

Each agent has golden datasets, schema-validity tests, provenance checks, hallucination tests, and regression metrics. Model replacement requires evaluation against the same baseline.
