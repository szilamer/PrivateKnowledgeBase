from uuid import UUID

from domain.errors import DomainError
from domain.proposals import ProposalFilter, ProposalStatus, ProposalType, RiskLevel
from fastapi import APIRouter, Depends, Query
from starlette.responses import JSONResponse

from api.dependencies import RequestServices, domain_error_response, get_services
from api.schemas.proposals import (
    ApproveRequest,
    AutoApproveResponse,
    BatchApproveRequest,
    DeferRequest,
    EditApproveRequest,
    EvidenceResponse,
    MergeEntitiesRequest,
    ProposalListResponse,
    ProposalResponse,
    RejectRequest,
)

router = APIRouter(tags=["proposals"])


def _to_response(proposal: object) -> ProposalResponse:
    from domain.proposals import KnowledgeProposal

    assert isinstance(proposal, KnowledgeProposal)
    return ProposalResponse(
        id=proposal.id,
        proposal_type=proposal.proposal_type.value,
        status=proposal.status.value,
        risk_level=proposal.risk_level.value,
        confidence=proposal.confidence,
        title=proposal.title,
        payload=proposal.payload,
        project_id=proposal.project_id,
        source_id=proposal.source_id,
        requires_review=proposal.requires_review,
        created_at=proposal.created_at,
        updated_at=proposal.updated_at,
        evidence=[
            EvidenceResponse(
                id=span.id,
                source_object_version_id=span.source_object_version_id,
                content_chunk_id=span.content_chunk_id,
                anchor_start=span.anchor_start,
                anchor_end=span.anchor_end,
                excerpt=span.excerpt,
            )
            for span in proposal.evidence
        ],
    )


@router.get("/proposals", response_model=ProposalListResponse)
async def list_proposals(
    services: RequestServices = Depends(get_services),
    status: ProposalStatus | None = Query(default=ProposalStatus.PENDING),
    proposal_type: ProposalType | None = Query(default=None),
    risk_level: RiskLevel | None = Query(default=None),
    source_id: UUID | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    cursor: UUID | None = Query(default=None),
) -> ProposalListResponse | JSONResponse:
    try:
        filters = ProposalFilter(
            status=status,
            proposal_type=proposal_type,
            risk_level=risk_level,
            source_id=source_id,
            limit=limit,
            cursor=cursor,
        )
        items, next_cursor = await services.proposals.list_proposals(services.owner, filters)
        return ProposalListResponse(
            items=[_to_response(item) for item in items],
            next_cursor=next_cursor,
        )
    except DomainError as exc:
        return JSONResponse(
            status_code=403,
            content=domain_error_response(exc, services.correlation_id),
        )


@router.get("/proposals/{proposal_id}", response_model=ProposalResponse)
async def get_proposal(
    proposal_id: UUID,
    services: RequestServices = Depends(get_services),
) -> ProposalResponse | JSONResponse:
    try:
        proposal = await services.proposals.get_proposal(services.owner, proposal_id)
        return _to_response(proposal)
    except DomainError as exc:
        return JSONResponse(
            status_code=404,
            content=domain_error_response(exc, services.correlation_id),
        )


@router.post("/proposals/{proposal_id}/approve", response_model=ProposalResponse)
async def approve_proposal(
    proposal_id: UUID,
    body: ApproveRequest,
    services: RequestServices = Depends(get_services),
) -> ProposalResponse | JSONResponse:
    try:
        proposal = await services.proposals.approve(
            services.owner,
            proposal_id,
            rationale=body.rationale,
            correlation_id=services.correlation_id,
        )
        return _to_response(proposal)
    except DomainError as exc:
        return JSONResponse(
            status_code=400,
            content=domain_error_response(exc, services.correlation_id),
        )


@router.post("/proposals/{proposal_id}/reject", response_model=ProposalResponse)
async def reject_proposal(
    proposal_id: UUID,
    body: RejectRequest,
    services: RequestServices = Depends(get_services),
) -> ProposalResponse | JSONResponse:
    try:
        proposal = await services.proposals.reject(
            services.owner,
            proposal_id,
            rationale=body.rationale,
            correlation_id=services.correlation_id,
        )
        return _to_response(proposal)
    except DomainError as exc:
        return JSONResponse(
            status_code=400,
            content=domain_error_response(exc, services.correlation_id),
        )


@router.post("/proposals/{proposal_id}/defer", response_model=ProposalResponse)
async def defer_proposal(
    proposal_id: UUID,
    body: DeferRequest,
    services: RequestServices = Depends(get_services),
) -> ProposalResponse | JSONResponse:
    try:
        proposal = await services.proposals.defer(
            services.owner,
            proposal_id,
            rationale=body.rationale,
            correlation_id=services.correlation_id,
        )
        return _to_response(proposal)
    except DomainError as exc:
        return JSONResponse(
            status_code=400,
            content=domain_error_response(exc, services.correlation_id),
        )


@router.post("/proposals/{proposal_id}/edit-and-approve", response_model=ProposalResponse)
async def edit_and_approve_proposal(
    proposal_id: UUID,
    body: EditApproveRequest,
    services: RequestServices = Depends(get_services),
) -> ProposalResponse | JSONResponse:
    try:
        proposal = await services.proposals.edit_and_approve(
            services.owner,
            proposal_id,
            edited_payload=body.edited_payload,
            rationale=body.rationale,
            correlation_id=services.correlation_id,
        )
        return _to_response(proposal)
    except DomainError as exc:
        return JSONResponse(
            status_code=400,
            content=domain_error_response(exc, services.correlation_id),
        )


@router.post("/proposals/{proposal_id}/merge", response_model=ProposalResponse)
async def merge_entity_proposal(
    proposal_id: UUID,
    body: MergeEntitiesRequest,
    services: RequestServices = Depends(get_services),
) -> ProposalResponse | JSONResponse:
    try:
        proposal = await services.proposals.merge_entities(
            services.owner,
            proposal_id,
            source_entity_id=body.source_entity_id,
            target_entity_id=body.target_entity_id,
            rationale=body.rationale,
            correlation_id=services.correlation_id,
        )
        return _to_response(proposal)
    except DomainError as exc:
        return JSONResponse(
            status_code=400,
            content=domain_error_response(exc, services.correlation_id),
        )


@router.post("/proposals/auto-approve", response_model=AutoApproveResponse)
async def auto_approve_proposals(
    services: RequestServices = Depends(get_services),
) -> AutoApproveResponse | JSONResponse:
    try:
        approved = await services.proposals.auto_approve_confident(
            services.owner,
            correlation_id=services.correlation_id,
        )
        count = len(approved)
        return AutoApproveResponse(
            approved_count=count,
            message=(
                f"{count} javaslat automatikusan jóváhagyva (80%+ bizonyosság)."
                if count
                else "Nincs automatikusan jóváhagyható javaslat."
            ),
        )
    except DomainError as exc:
        return JSONResponse(
            status_code=400,
            content=domain_error_response(exc, services.correlation_id),
        )


@router.post("/proposals/batch-approve", response_model=ProposalListResponse)
async def batch_approve_proposals(
    body: BatchApproveRequest,
    services: RequestServices = Depends(get_services),
) -> ProposalListResponse | JSONResponse:
    try:
        approved = await services.proposals.batch_approve(
            services.owner,
            body.proposal_ids,
            correlation_id=services.correlation_id,
        )
        return ProposalListResponse(
            items=[_to_response(item) for item in approved],
            next_cursor=None,
        )
    except DomainError as exc:
        return JSONResponse(
            status_code=400,
            content=domain_error_response(exc, services.correlation_id),
        )
