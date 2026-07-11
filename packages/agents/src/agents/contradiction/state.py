from typing import TypedDict
from uuid import UUID

from domain.canonical import CanonicalClaim, ContradictionFinding
from domain.proposals import KnowledgeProposal


class ContradictionState(TypedDict, total=False):
    owner_id: UUID
    claim: CanonicalClaim
    proposal: KnowledgeProposal
    candidates: list[CanonicalClaim]
    findings: list[ContradictionFinding]
    candidate_count: int
    pipeline_version: str
    error: str | None
