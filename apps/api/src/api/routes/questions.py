from domain.questions import QuestionRequest
from fastapi import APIRouter, Depends

from api.dependencies import RequestServices, get_services
from api.schemas.questions import (
    AnswerClaimResponse,
    CitationResponse,
    QuestionAnswerResponse,
    QuestionBody,
    RetrievalStepResponse,
)

router = APIRouter(tags=["questions"])


@router.post("/questions", response_model=QuestionAnswerResponse)
async def ask_question(
    body: QuestionBody,
    services: RequestServices = Depends(get_services),
) -> QuestionAnswerResponse:
    answer = await services.qa.ask(
        services.owner,
        QuestionRequest(question=body.question, mode=body.mode, limit=body.limit),
        correlation_id=services.correlation_id,
    )
    return QuestionAnswerResponse(
        question=answer.question,
        answer=answer.answer,
        confidence=answer.confidence,
        insufficient_evidence=answer.insufficient_evidence,
        citations=[
            CitationResponse(
                citation_id=item.citation_id,
                chunk_id=item.chunk_id,
                source_id=item.source_id,
                external_id=item.external_id,
                excerpt=item.excerpt,
                score=item.score,
                signal=item.signal.value,
            )
            for item in answer.citations
        ],
        claims=[
            AnswerClaimResponse(
                text=claim.text,
                confidence=claim.confidence,
                citation_ids=claim.citation_ids,
            )
            for claim in answer.claims
        ],
        related_entity_ids=answer.related_entity_ids,
        retrieval_plan=[
            RetrievalStepResponse(
                signal=step.signal.value,
                description=step.description,
                result_count=step.result_count,
            )
            for step in answer.retrieval_plan
        ],
        warnings=answer.warnings,
        conflicts=answer.conflicts,
        model=answer.model,
        created_at=answer.created_at,
    )
