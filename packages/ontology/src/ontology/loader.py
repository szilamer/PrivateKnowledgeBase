from pathlib import Path

import yaml  # type: ignore[import-untyped]
from pydantic import BaseModel, Field


class OntologyTypeDefinition(BaseModel):
    id: str
    label: str | None = None
    description: str | None = None


class OntologySnapshot(BaseModel):
    version: str = "0.0.0"
    entity_type_ids: list[str] = Field(default_factory=list)
    relationship_type_ids: list[str] = Field(default_factory=list)
    source_files: list[str] = Field(default_factory=list)


def default_definitions_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "definitions"


def load_ontology_snapshot(definitions_dir: Path | None = None) -> OntologySnapshot:
    """Read-only load of normative ontology YAML (ADR-011, Phase E-4)."""
    root = definitions_dir or default_definitions_dir()
    entity_ids: list[str] = []
    relationship_ids: list[str] = []
    versions: list[str] = []
    source_files: list[str] = []

    for path in sorted(root.glob("*.yaml")):
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            continue
        source_files.append(path.name)
        version = raw.get("version")
        if isinstance(version, str):
            versions.append(version)
        for entity in raw.get("entity_types") or []:
            if isinstance(entity, dict) and entity.get("id"):
                entity_ids.append(str(entity["id"]))
        for relationship in raw.get("relationship_types") or []:
            if isinstance(relationship, dict) and relationship.get("id"):
                relationship_ids.append(str(relationship["id"]))

    return OntologySnapshot(
        version=max(versions) if versions else "0.0.0",
        entity_type_ids=sorted(set(entity_ids)),
        relationship_type_ids=sorted(set(relationship_ids)),
        source_files=source_files,
    )
