from datetime import UTC, datetime
from uuid import UUID, uuid4

from domain.audit import AuditAction, AuditEvent
from domain.content import ChunkSearchHit, SearchRequest
from domain.identity import OwnerContext
from domain.questions import (
    Citation,
    QuestionAnswer,
    QuestionRequest,
    RetrievalPlanStep,
    RetrievalSignal,
)
from domain.retrieval import add_chunk_citation
from domain.retrieval_outcome import RETRIEVAL_PIPELINE_VERSION, RetrievalPlanningOutcome

from application.content.search import SearchService
from application.policy import LocalPolicyService
from application.ports.canonical import CanonicalRepository
from application.ports.graph import GraphRepository
from application.ports.knowledge import AuditWriter
from application.ports.qa import AnswerSynthesizer
from application.qa.synthesis_service import AnswerSynthesisService


class HybridRetrievalPlanner:
    """MVP-05 / EPIC-07 — combine keyword, semantic, graph, and canonical signals."""

    def __init__(
        self,
        search: SearchService,
        canonical: CanonicalRepository,
        graph: GraphRepository,
        policy: LocalPolicyService,
        *,
        planner_version: str = "graph_v2",
    ) -> None:
        self._search = search
        self._canonical = canonical
        self._graph = graph
        self._policy = policy
        self._planner_version = planner_version

    async def plan_and_retrieve(
        self, owner: OwnerContext, request: QuestionRequest
    ) -> RetrievalPlanningOutcome:
        self._policy.authorize_owner(owner, owner.owner_id)
        if request.mode == "hybrid" and self._planner_version == "graph_v2":
            return await self._plan_via_graph(owner, request)
        citations, plan, related_entities = await self._plan_deterministic(owner, request)
        ranked = citations[: request.limit]
        return RetrievalPlanningOutcome(
            citations=ranked,
            plan=plan,
            related_entity_ids=related_entities,
            citation_ids=[item.citation_id for item in ranked],
            pipeline_version="deterministic",
        )

    async def _plan_via_graph(
        self, owner: OwnerContext, request: QuestionRequest
    ) -> RetrievalPlanningOutcome:
        from agents.retrieval.graph import build_retrieval_graph

        owner_id = owner.owner_id

        async def search_chunks(
            requested_owner: UUID,
            question: str,
            mode: str,
            limit: int,
        ) -> list[ChunkSearchHit]:
            result = await self._search.search(
                owner,
                SearchRequest(query=question, mode=mode, limit=limit),
            )
            return result.hits

        from domain.canonical import CanonicalClaim, CanonicalEntity
        from domain.graph import GraphView

        async def find_matching_entities(
            requested_owner: UUID, question: str
        ) -> list[CanonicalEntity]:
            assert requested_owner == owner_id
            return await self._canonical.search_entities_by_query(
                requested_owner, question, limit=5
            )

        async def expand_neighborhood(requested_owner: UUID, entity_id: UUID) -> GraphView:
            assert requested_owner == owner_id
            return await self._graph.get_entity_neighborhood(
                requested_owner, entity_id, depth=1, limit=20
            )

        async def lookup_claims(
            requested_owner: UUID, question: str, limit: int
        ) -> list[CanonicalClaim]:
            assert requested_owner == owner_id
            return await self._canonical.search_claims_by_query(
                requested_owner, question, limit=limit
            )

        graph = build_retrieval_graph(
            search_chunks=search_chunks,
            find_matching_entities=find_matching_entities,
            expand_neighborhood=expand_neighborhood,
            search_claims=lookup_claims,
        )
        final = await graph.ainvoke(
            {
                "owner_id": owner_id,
                "question": request.question,
                "mode": request.mode,
                "limit": request.limit,
                "citations": {},
                "plan": [],
                "related_entities": [],
            }
        )
        citations_map = final.get("citations", {})
        ranked = list(citations_map.values())
        return RetrievalPlanningOutcome(
            citations=ranked,
            plan=list(final.get("plan", [])),
            related_entity_ids=list(final.get("related_entities", [])),
            citation_ids=list(final.get("citation_ids", [])),
            pipeline_version=str(final.get("pipeline_version", RETRIEVAL_PIPELINE_VERSION)),
        )

    async def _plan_deterministic(
        self, owner: OwnerContext, request: QuestionRequest
    ) -> tuple[list[Citation], list[RetrievalPlanStep], list[UUID]]:
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
            add_chunk_citation(citations, hit, signal=signal)
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
        return ranked, plan, list(dict.fromkeys(related_entities))


class QuestionAnsweringService:
    """MVP-06 — source-backed Q&A with citations (FR-RET-003..005)."""

    def __init__(
        self,
        planner: HybridRetrievalPlanner,
        synthesizer: AnswerSynthesizer,
        policy: LocalPolicyService,
        audit: AuditWriter | None = None,
        *,
        synthesis: AnswerSynthesisService | None = None,
    ) -> None:
        self._planner = planner
        self._synthesizer = synthesizer
        self._policy = policy
        self._audit = audit
        self._synthesis = synthesis or AnswerSynthesisService(use_graph=True)

    async def ask(
        self,
        owner: OwnerContext,
        request: QuestionRequest,
        *,
        correlation_id: str,
    ) -> QuestionAnswer:
        self._policy.authorize_owner(owner, owner.owner_id)
        outcome = await self._planner.plan_and_retrieve(owner, request)
        citations = outcome.citations
        plan = outcome.plan
        related_entities = outcome.related_entity_ids

        await self._record_retrieval_plan(
            owner,
            request,
            plan=plan,
            citation_ids=outcome.citation_ids,
            pipeline_version=outcome.pipeline_version,
            correlation_id=correlation_id,
        )

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

        answer = await self._synthesis.synthesize(
            request.question,
            citations,
            synthesizer=self._synthesizer,
        )
        answer.retrieval_plan = plan
        answer.related_entity_ids = related_entities
        return answer

    async def _record_retrieval_plan(
        self,
        owner: OwnerContext,
        request: QuestionRequest,
        *,
        plan: list[RetrievalPlanStep],
        citation_ids: list[str],
        pipeline_version: str,
        correlation_id: str,
    ) -> None:
        if self._audit is None or not hasattr(self._audit, "append"):
            return
        event = AuditEvent(
            id=uuid4(),
            actor_id=owner.owner_id,
            action=AuditAction.RETRIEVAL_PLANNED,
            object_type="question_answer",
            object_id=uuid4(),
            correlation_id=correlation_id,
            metadata={
                "question": request.question,
                "mode": request.mode,
                "pipeline_version": pipeline_version,
                "citation_ids": citation_ids,
                "plan": [step.model_dump(mode="json") for step in plan],
            },
            created_at=datetime.now(UTC),
        )
        await self._audit.append(event)
