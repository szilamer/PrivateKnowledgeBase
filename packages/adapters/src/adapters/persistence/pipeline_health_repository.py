import json

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class PostgresPipelineHealthRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def count_by_status(self, column: str, status: str) -> int:
        allowed = {"extraction_status", "knowledge_status", "triage_status"}
        if column not in allowed:
            return 0
        result = await self._session.execute(
            text(
                f"""
                SELECT COUNT(*) AS count
                FROM source_object_versions
                WHERE {column} = :status
                """
            ),
            {"status": status},
        )
        row = result.first()
        return 0 if row is None else int(dict(row._mapping)["count"])

    async def count_embedding_model_mismatch_versions(self, current_model: str) -> int:
        result = await self._session.execute(
            text(
                """
                SELECT COUNT(DISTINCT sov.id) AS count
                FROM source_object_versions sov
                JOIN content_chunks cc ON cc.source_object_version_id = sov.id
                WHERE cc.embedding_model IS NOT NULL
                  AND cc.embedding_model != :current_model
                  AND COALESCE(
                        (sov.maintenance_flags->>'embedding_model_mismatch')::boolean,
                        false
                      ) = false
                """
            ),
            {"current_model": current_model},
        )
        row = result.first()
        return 0 if row is None else int(dict(row._mapping)["count"])

    async def flag_embedding_model_mismatch(self, current_model: str) -> int:
        result = await self._session.execute(
            text(
                """
                UPDATE source_object_versions sov
                SET maintenance_flags = COALESCE(sov.maintenance_flags, '{}'::jsonb)
                    || CAST(:flag AS jsonb)
                FROM content_chunks cc
                WHERE cc.source_object_version_id = sov.id
                  AND cc.embedding_model IS NOT NULL
                  AND cc.embedding_model != :current_model
                  AND COALESCE(
                        (sov.maintenance_flags->>'embedding_model_mismatch')::boolean,
                        false
                      ) = false
                RETURNING sov.id
                """
            ),
            {
                "current_model": current_model,
                "flag": json.dumps({"embedding_model_mismatch": True}),
            },
        )
        return len(result.fetchall())

    async def get_pipeline_snapshot(self, current_embedding_model: str) -> dict[str, int]:
        triage_pending = await self._session.execute(
            text(
                """
                SELECT COUNT(*) AS count
                FROM source_object_versions
                WHERE triage_status = 'pending'
                  AND extraction_status = 'pending'
                """
            )
        )
        triage_row = triage_pending.first()
        return {
            "extraction_pending": await self.count_by_status("extraction_status", "pending"),
            "extraction_failed": await self.count_by_status("extraction_status", "failed"),
            "knowledge_pending": await self.count_by_status("knowledge_status", "pending"),
            "triage_pending": 0 if triage_row is None else int(dict(triage_row._mapping)["count"]),
            "embedding_model_mismatch_versions": await self.count_embedding_model_mismatch_versions(
                current_embedding_model
            ),
        }
