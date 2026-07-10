# ADR-011: Physical Representation of the Ontology

**Status:** Accepted  
**Decision date:** 2026-07-10

## Decision

The normative ontology lives in version-controlled YAML files containing entity types, relationship types, fields, validation rules, and deprecated aliases. The system validates and loads the ontology at startup or migration. Runtime instances appear in PostgreSQL and Neo4j, but these stores are not the schema source of truth. AI may create only an `OntologyProposal`; acceptance requires a human-reviewed YAML change and version increment.

## Consequences

Ontology changes require code review. Types are deprecated and migrated rather than immediately deleted. Every claim records the ontology version.
