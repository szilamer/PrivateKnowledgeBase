from datetime import UTC, datetime
from uuid import UUID

from domain.content import ChunkSearchHit, SearchRequest
from domain.identity import OwnerContext
from domain.questions import (
    Citation,
    QuestionAnswer,
    QuestionRequest,
    RetrievalPlanStep,
    RetrievalSignal,
)

from application.content.search import SearchService
from application.policy import LocalPolicyService
from application.ports.canonical import CanonicalRepository
from application.ports.graph import GraphRepository
from application.ports.qa import AnswerSynthesizer


class HybridRetrievalPlanner:
    """MVP-05 / EPIC-07 — combine keyword, semantic, graph, and canonical signals."""

    def __init__(
        self,
        search: SearchService,
        canonical: CanonicalRepository,
        graph: GraphRepository,
        policy: LocalPolicyService,
    ) -> None:
        self._search = search
        self._canonical = canonical
        self._graph = graph
        self._policy = policy

    async def plan_and_retrieve(
        self, owner: OwnerContext, request: QuestionRequest
    ) -> tuple[list[Citation], list[RetrievalPlanStep], list[UUID]]:
        self._policy.authorize_owner(owner, owner.owner_id)
        citations: dict[str, Citation] = {}
        plan: list[RetrievalPlanStep] = []
        related_entities: list[UUID] = []

        search_result = await self._search.search(
            owner,
            SearchRequest(query=request.question, mode=request.mode, limit=request.limit),
        )
        signal = (
            RetrievalSignal.KEYWORD
            if request.mode == "keyword"
            else RetrievalSignal.SEMANTIC
            if request.mode == "semantic"
            else RetrievalSignal.KEYWORD
        )
        for hit in search_result.hits:
            self._add_chunk_hit(citations, hit, signal=signal)
        plan.append(
            RetrievalPlanStep(
                signal=signal if request.mode != "hybrid" else RetrievalSignal.KEYWORD,
                description=f"{request.mode} chunk search",
                result_count=len(search_result.hits),
            )
        )

        matching_entities = await self._canonical.search_entities_by_query(
            owner.owner_id, request.question, limit=5
        )
        for entity in matching_entities:
            related_entities.append(entity.id)
            graph_view = await self._graph.get_entity_neighborhood(
                owner.owner_id, entity.id, depth=1, limit=20
            )
            for node in graph_view.nodes:
                if node.node_type == "entity":
                    citations[f"graph-{node.id}"] = Citation(
                        citation_id=f"graph-{node.id}",
                        excerpt=f"Graph entity: {node.label}",
                        score=0.5,
                        signal=RetrievalSignal.GRAPH,
                    )
        plan.append(
            RetrievalPlanStep(
                signal=RetrievalSignal.GRAPH,
                description="entity neighborhood expansion",
                result_count=len(matching_entities),
            )
        )

        claims = await self._canonical.search_claims_by_query(
            owner.owner_id, request.question, limit=request.limit
        )
        for claim in claims:
            cite_id = f"claim-{claim.id}"
            citations[cite_id] = Citation(
                citation_id=cite_id,
                excerpt=f"{claim.predicate}: {claim.object_value}",
                score=float(claim.confidence),
                signal=RetrievalSignal.CANONICAL,
            )
            if claim.subject_entity_id:
                related_entities.append(claim.subject_entity_id)
        plan.append(
            RetrievalPlanStep(
                signal=RetrievalSignal.CANONICAL,
                description="canonical claim lookup",
                result_count=len(claims),
            )
        )

        ranked = sorted(citations.values(), key=lambda item: item.score, reverse=True)
        return ranked[: request.limit], plan, list(dict.fromkeys(related_entities))

    def _add_chunk_hit(
        self,
        citations: dict[str, Citation],
        hit: ChunkSearchHit,
        *,
        signal: RetrievalSignal,
    ) -> None:
        cite_id = f"chunk-{hit.chunk_id}"
        citations[cite_id] = Citation(
            citation_id=cite_id,
            chunk_id=hit.chunk_id,
            source_id=hit.source_id,
            source_object_version_id=hit.source_object_version_id,
            external_id=hit.external_id,
            excerpt=hit.text[:500],
            score=hit.score,
            signal=signal,
        )


class QuestionAnsweringService:
    """MVP-06 — source-backed Q&A with citations (FR-RET-003..005)."""

    def __init__(
        self,
        planner: HybridRetrievalPlanner,
        synthesizer: AnswerSynthesizer,
        policy: LocalPolicyService,
    ) -> None:
        self._planner = planner
        self._synthesizer = synthesizer
        self._policy = policy

    async def ask(self, owner: OwnerContext, request: QuestionRequest) -> QuestionAnswer:
        self._policy.authorize_owner(owner, owner.owner_id)
        citations, plan, related_entities = await self._planner.plan_and_retrieve(owner, request)

        if not citations:
            now = datetime.now(UTC)
            return QuestionAnswer(
                question=request.question,
                answer=(
                    "Insufficient evidence to answer this question. "
                    "Try syncing sources and approving knowledge proposals first."
                ),
                confidence=0.0,
                insufficient_evidence=True,
                retrieval_plan=plan,
                created_at=now,
            )

        answer = await self._synthesizer.synthesize(request.question, citations)
        answer.retrieval_plan = plan
        answer.related_entity_ids = related_entities
        return answer
