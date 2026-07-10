import re
from uuid import UUID

from domain.entities import EntityType
from domain.extraction import (
    EXTRACTION_SCHEMA_VERSION,
    ExtractedClaim,
    ExtractedDecision,
    ExtractedEntity,
    ExtractedEvent,
    ExtractedRelationship,
    ExtractedTask,
    ExtractionResult,
)

_TECH_PATTERN = re.compile(
    r"\b(Python|TypeScript|JavaScript|PostgreSQL|Redis|Neo4j|Docker|FastAPI|"
    r"Next\.js|Celery|LangGraph|GitHub)\b",
    re.IGNORECASE,
)
_TODO_PATTERN = re.compile(r"(?:TODO|TASK)[:\s]+(.+)", re.IGNORECASE)
_DECISION_PATTERN = re.compile(r"(?:decided|decision)[:\s]+(.+)", re.IGNORECASE | re.MULTILINE)
_EVENT_PATTERN = re.compile(
    r"(?:meeting|release|deployed|shipped)[:\s]+(.+)", re.IGNORECASE | re.MULTILINE
)
_HEADER_PATTERN = re.compile(r"^#{1,3}\s+(.+)$", re.MULTILINE)
_PERSON_PATTERN = re.compile(r"\b([A-Z][a-z]+ [A-Z][a-z]+)\b")


def _entity_type_for_header(title: str) -> EntityType:
    lowered = title.lower()
    if "project" in lowered:
        return EntityType.PROJECT
    if "repository" in lowered or "repo" in lowered:
        return EntityType.REPOSITORY
    return EntityType.CONCEPT


class HeuristicExtractor:
    """Deterministic fallback extractor for offline CI and LLM failures."""

    def extract(self, text: str, chunks: list[tuple[UUID, str]]) -> ExtractionResult:
        entities: list[ExtractedEntity] = []
        tasks: list[ExtractedTask] = []
        decisions: list[ExtractedDecision] = []
        events: list[ExtractedEvent] = []
        claims: list[ExtractedClaim] = []
        relationships: list[ExtractedRelationship] = []
        warnings: list[str] = []

        chunk_map = {chunk_id: body for chunk_id, body in chunks}
        default_chunk = chunks[0][0] if chunks else None

        for match in _HEADER_PATTERN.finditer(text):
            title = match.group(1).strip()
            entities.append(
                ExtractedEntity(
                    local_id=f"ent-{len(entities)}",
                    name=title,
                    entity_type=_entity_type_for_header(title),
                    confidence=0.75,
                    chunk_id=default_chunk,
                    anchor_start=match.start(),
                    anchor_end=match.end(),
                )
            )

        seen_tech: set[str] = set()
        for match in _TECH_PATTERN.finditer(text):
            name = match.group(1)
            key = name.lower()
            if key in seen_tech:
                continue
            seen_tech.add(key)
            entities.append(
                ExtractedEntity(
                    local_id=f"ent-tech-{len(entities)}",
                    name=name,
                    entity_type=EntityType.TECHNOLOGY,
                    confidence=0.82,
                    chunk_id=default_chunk,
                    anchor_start=match.start(),
                    anchor_end=match.end(),
                )
            )

        for match in _PERSON_PATTERN.finditer(text):
            name = match.group(1)
            entities.append(
                ExtractedEntity(
                    local_id=f"ent-person-{len(entities)}",
                    name=name,
                    entity_type=EntityType.PERSON,
                    confidence=0.65,
                    chunk_id=default_chunk,
                    anchor_start=match.start(),
                    anchor_end=match.end(),
                )
            )

        for match in _TODO_PATTERN.finditer(text):
            tasks.append(
                ExtractedTask(
                    local_id=f"task-{len(tasks)}",
                    title=match.group(1).strip()[:200],
                    status="open",
                    confidence=0.78,
                    chunk_id=default_chunk,
                )
            )

        for match in _DECISION_PATTERN.finditer(text):
            decisions.append(
                ExtractedDecision(
                    local_id=f"decision-{len(decisions)}",
                    title=match.group(1).strip()[:200],
                    status="proposed",
                    confidence=0.7,
                    chunk_id=default_chunk,
                )
            )

        for match in _EVENT_PATTERN.finditer(text):
            events.append(
                ExtractedEvent(
                    local_id=f"event-{len(events)}",
                    title=match.group(1).strip()[:200],
                    event_type="occurrence",
                    confidence=0.68,
                    chunk_id=default_chunk,
                )
            )

        if entities and len(entities) >= 2:
            relationships.append(
                ExtractedRelationship(
                    local_id="rel-0",
                    source_local_id=entities[0].local_id,
                    target_local_id=entities[1].local_id,
                    relationship_type="MENTIONS",
                    confidence=0.6,
                    chunk_id=default_chunk,
                )
            )
            claims.append(
                ExtractedClaim(
                    local_id="claim-0",
                    subject_local_id=entities[0].local_id,
                    predicate="mentions",
                    value=entities[1].name,
                    confidence=0.6,
                    chunk_id=default_chunk,
                )
            )

        if not entities and not tasks and not decisions:
            warnings.append("heuristic_extractor_found_no_signals")
            _ = chunk_map

        return ExtractionResult(
            schema_version=EXTRACTION_SCHEMA_VERSION,
            entities=entities,
            claims=claims,
            relationships=relationships,
            tasks=tasks,
            decisions=decisions,
            events=events,
            warnings=warnings,
        )
