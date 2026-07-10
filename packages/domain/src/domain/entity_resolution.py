import re

from domain.entities import EntityMatch, EntityType
from domain.extraction import ExtractedEntity

_MATCH_THRESHOLD = 0.72
_AMBIGUITY_GAP = 0.08


def normalize_name(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip().lower())


def name_similarity(left: str, right: str) -> float:
    a = normalize_name(left)
    b = normalize_name(right)
    if a == b:
        return 1.0
    if a in b or b in a:
        shorter = min(len(a), len(b))
        longer = max(len(a), len(b))
        return shorter / longer if longer else 0.0
    a_tokens = set(a.split())
    b_tokens = set(b.split())
    if not a_tokens or not b_tokens:
        return 0.0
    overlap = len(a_tokens & b_tokens)
    return overlap / max(len(a_tokens), len(b_tokens))


def resolve_entity(
    entity: ExtractedEntity,
    candidates: list[EntityMatch],
) -> tuple[str, list[EntityMatch]]:
    """Return resolution action: new | link | ambiguous."""
    scored = sorted(candidates, key=lambda item: item.score, reverse=True)
    if not scored:
        return "new", []

    best = scored[0]
    if best.score < _MATCH_THRESHOLD:
        return "new", scored

    if len(scored) > 1 and (best.score - scored[1].score) < _AMBIGUITY_GAP:
        return "ambiguous", scored[:3]

    return "link", [best]


def classify_risk(entity_type: EntityType, confidence: float) -> str:
    if confidence < 0.6:
        return "high"
    if confidence >= 0.85 and entity_type in {
        EntityType.TECHNOLOGY,
        EntityType.CONCEPT,
        EntityType.DOCUMENT,
    }:
        return "low"
    return "medium"


def requires_review(risk_level: str, proposal_type: str) -> bool:
    if risk_level == "high":
        return True
    if proposal_type == "entity_resolution":
        return True
    return risk_level != "low"
