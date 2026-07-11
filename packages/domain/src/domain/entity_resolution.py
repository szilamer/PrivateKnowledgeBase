import re

from domain.entities import EntityMatch, EntityType
from domain.entity_resolution_outcome import EntityResolutionProposalSpec
from domain.extraction import ExtractedEntity
from domain.proposals import ProposalType

_MATCH_THRESHOLD = 0.72
_AMBIGUITY_GAP = 0.08
AUTO_APPROVE_CONFIDENCE = 0.8


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


def merge_alias_lists(existing: list[str], additions: list[str]) -> list[str]:
    """Deduplicate aliases case-insensitively while preserving first-seen casing."""
    merged: list[str] = []
    seen: set[str] = set()
    for name in [*existing, *additions]:
        normalized = normalize_name(name)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        merged.append(name.strip())
    return merged


def build_entity_resolution_spec(
    entity: ExtractedEntity,
    action: str,
    matches: list[EntityMatch],
) -> EntityResolutionProposalSpec:
    """Map deterministic resolution action to proposal type and payload."""
    risk = classify_risk(entity.entity_type, entity.confidence)
    proposal_type = ProposalType.ENTITY_RESOLUTION if action == "ambiguous" else ProposalType.ENTITY
    payload: dict[str, object] = entity.model_dump(mode="json")
    payload["resolution_action"] = action
    if action == "link" and matches:
        payload["resolved_entity_id"] = str(matches[0].entity_id)
    if action == "ambiguous":
        payload["candidates"] = [match.model_dump(mode="json") for match in matches]
    elif matches:
        payload["ranked_candidates"] = [match.model_dump(mode="json") for match in matches[:5]]

    needs_review = requires_review(risk, proposal_type.value, confidence=entity.confidence)
    return EntityResolutionProposalSpec(
        entity=entity,
        resolution_action=action,
        proposal_type=proposal_type,
        payload=payload,
        needs_review=needs_review,
        risk_level=risk,
        candidates=matches[:5] if action == "ambiguous" else matches[:1],
    )


def requires_review(
    risk_level: str,
    proposal_type: str,
    *,
    confidence: float | None = None,
) -> bool:
    if proposal_type in {"entity_resolution", "merge"}:
        return True
    if proposal_type == "relationship":
        return True
    if risk_level == "high":
        return True
    if confidence is not None and confidence >= AUTO_APPROVE_CONFIDENCE:
        return False
    return risk_level != "low"
