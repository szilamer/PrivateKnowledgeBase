# ADR-010: Document Processing Pipeline

**Status:** Accepted  
**Decision date:** 2026-07-10

## Decision

Document processing uses parser adapters by type. MVP priority is: (1) Markdown and plain text, (2) HTML and email, (3) PDF, (4) DOCX, and (5) source code and repository metadata. The original object or verifiable reference remains unchanged. Extracted text, structure, chunks, and claims are separately versioned derivatives.

## Rules

OCR runs only when no usable text layer exists. Every derivative records parser and pipeline versions. Partial page or attachment failure remains visible.
