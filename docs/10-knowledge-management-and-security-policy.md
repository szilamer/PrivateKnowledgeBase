# Knowledge Management, Security, and Authorization Policy

**Version:** 0.1  
**Status:** Draft

## 1. Data classification

Every source and derived object has an owner, visibility, and sensitivity classification. Initial sensitivity levels are public, internal, confidential, and restricted.

## 2. Source-of-truth policy

Original source systems remain authoritative. Derived content is identified as extracted, inferred, approved, superseded, or retracted. The system never represents an unapproved inference as an original source statement.

## 3. Least privilege

Connectors receive only the permissions required for configured scopes. Tokens are stored as secrets. Access is checked at the application-service boundary and incorporated into retrieval queries.

## 4. External model policy

Before content is sent to an external provider, a policy decision evaluates source, sensitivity, owner policy, provider, purpose, and requested data fields. Restricted content remains local unless explicitly authorized.

## 5. Logging

Logs contain identifiers and diagnostics, not complete documents, credentials, or unrestricted prompts. Sensitive values are masked. Debug sampling requires explicit configuration.

## 6. Retention and deletion

Source references, derived content, embeddings, proposals, canonical claims, and audit records have separate retention rules. Deletion requests produce an impact report and preserve legally or operationally required audit metadata.

## 7. Backup and export

The owner can export structured domain data, ontology versions, source references, and audit records. Backup and restore procedures cover PostgreSQL configuration and the ability to rebuild Neo4j.

## 8. Future agent-to-agent access

External agents use service accounts with explicit scopes, project filters, purpose limitations, rate limits, and audit. No agent receives unrestricted graph access by default.
