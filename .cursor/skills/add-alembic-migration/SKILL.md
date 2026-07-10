---
name: add-alembic-migration
description: Create a reversible Alembic migration for PostgreSQL schema changes. Use when adding tables for sources, ingestion, knowledge, audit, or outbox.
---

# Add Alembic Migration

## Steps

1. **Design** — align with schema groups in `docs/07-technical-specification.md` §4:
   identity, sources, ingestion, content, knowledge, approval, ontology metadata, audit, outbox
2. **Create revision** in `apps/api/alembic/versions/`:
   - Naming: `000X_descriptive_name.py`
   - Both `upgrade()` and `downgrade()` implemented
3. **Conventions**:
   - UUID primary keys with `gen_random_uuid()` (requires `pgcrypto`)
   - `created_at`, `updated_at` TIMESTAMPTZ on mutable rows
   - Optimistic versioning on mutable aggregates where appropriate
   - pgvector columns: store model, dimension, content hash
4. **Outbox** — canonical writes that trigger projection include outbox event in same transaction
5. **Verify locally**:
   ```bash
   cd apps/api && uv run alembic upgrade head && uv run alembic downgrade -1 && uv run alembic upgrade head
   ```

## Do not

- Drop production data without explicit migration path
- Mix embedding models in one vector index
