import json
from uuid import UUID

from application.ports.content import VersionContentRepository
from domain.triage import TriageClassification


class VersionTriageService:
    """Phase B — classify pending source versions before extraction ordering."""

    def __init__(self, versions: VersionContentRepository) -> None:
        self._versions = versions

    async def process_pending(self, *, batch_size: int = 50) -> int:
        pending = await self._versions.get_versions_needing_triage(limit=batch_size)
        processed = 0
        for row in pending:
            version_id = UUID(str(row["version_id"]))
            classification = await self.classify_version(row)
            await self._versions.save_triage(
                version_id,
                status="completed",
                metadata=classification.model_dump(mode="json"),
            )
            processed += 1
        return processed

    async def classify_version(self, record: dict[str, object]) -> TriageClassification:
        from agents.triage.graph import build_triage_graph

        configuration = record.get("configuration") or {}
        if isinstance(configuration, str):
            try:
                configuration = json.loads(configuration)
            except json.JSONDecodeError:
                configuration = {}
        if not isinstance(configuration, dict):
            configuration = {}

        graph = build_triage_graph()
        final = await graph.ainvoke(
            {
                "version_id": UUID(str(record["version_id"])),
                "external_id": str(record.get("external_id", "")),
                "mime_type": str(record["mime_type"]) if record.get("mime_type") else None,
                "source_configuration": configuration,
            }
        )
        classification = final.get("classification")
        if isinstance(classification, TriageClassification):
            return classification
        return TriageClassification.model_validate(classification)
