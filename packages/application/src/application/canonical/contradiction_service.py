from datetime import datetime
from uuid import UUID

from domain.canonical import CanonicalClaim
from domain.contradiction_outcome import ContradictionDetectionOutcome
from domain.proposals import KnowledgeProposal

from application.ports.canonical import CanonicalRepository


class ContradictionDetectionService:
    """Phase D — compare new claims against active canonical claims via LangGraph."""

    def __init__(self, canonical: CanonicalRepository) -> None:
        self._canonical = canonical

    async def detect_for_claim(
        self,
        owner_id: UUID,
        claim: CanonicalClaim,
        proposal: KnowledgeProposal,
        *,
        now: datetime,
    ) -> ContradictionDetectionOutcome:
        from agents.contradiction.graph import build_contradiction_graph

        async def load_candidates(
            owner_id: UUID,
            subject_entity_id: UUID | None,
            predicate: str,
        ) -> list[CanonicalClaim]:
            return await self._canonical.find_active_claims(
                owner_id,
                subject_entity_id=subject_entity_id,
                predicate=predicate,
            )

        graph = build_contradiction_graph(
            load_candidate_claims=load_candidates,
            now=now,
        )
        final = await graph.ainvoke(
            {
                "owner_id": owner_id,
                "claim": claim,
                "proposal": proposal,
            }
        )
        findings = list(final.get("findings", []))
        return ContradictionDetectionOutcome(
            findings=findings,
            candidate_count=int(final.get("candidate_count", 0)),
        )
