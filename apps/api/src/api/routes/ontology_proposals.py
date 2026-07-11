from uuid import UUID

from domain.errors import DomainError
from domain.ontology_proposals import OntologyProposalStatus
from fastapi import APIRouter, Depends, Query
from starlette.responses import JSONResponse

from api.dependencies import RequestServices, domain_error_response, get_services
from api.schemas.ontology import (
    OntologyDecisionRequest,
    OntologyProposalListResponse,
    OntologyProposalResponse,
    OntologyScanResponse,
)

router = APIRouter(tags=["ontology"])


def _to_response(proposal: object) -> OntologyProposalResponse:
    from domain.ontology_proposals import OntologyProposal

    assert isinstance(proposal, OntologyProposal)
    return OntologyProposalResponse(
        id=str(proposal.id),
        kind=proposal.kind.value,
        status=proposal.status.value,
        title=proposal.title,
        rationale=proposal.rationale,
        proposed_definition=proposal.proposed_definition,
        evidence=proposal.evidence,
        ontology_version=proposal.ontology_version,
        decision_rationale=proposal.decision_rationale,
        created_at=proposal.created_at,
        updated_at=proposal.updated_at,
        decided_at=proposal.decided_at,
    )


@router.get("/ontology-proposals", response_model=OntologyProposalListResponse)
async def list_ontology_proposals(
    services: RequestServices = Depends(get_services),
    status: OntologyProposalStatus | None = Query(default=OntologyProposalStatus.PENDING),
    limit: int = Query(default=50, ge=1, le=100),
) -> OntologyProposalListResponse | JSONResponse:
    try:
        items = await services.ontology.list_proposals(
            services.owner,
            status=status,
            limit=limit,
        )
        return OntologyProposalListResponse(items=[_to_response(item) for item in items])
    except DomainError as exc:
        return JSONResponse(
            status_code=400,
            content=domain_error_response(exc, services.correlation_id),
        )


@router.get("/ontology-proposals/{proposal_id}", response_model=OntologyProposalResponse)
async def get_ontology_proposal(
    proposal_id: UUID,
    services: RequestServices = Depends(get_services),
) -> OntologyProposalResponse | JSONResponse:
    try:
        proposal = await services.ontology.get_proposal(services.owner, proposal_id)
        return _to_response(proposal)
    except DomainError as exc:
        return JSONResponse(
            status_code=404,
            content=domain_error_response(exc, services.correlation_id),
        )


@router.post("/ontology-proposals/scan", response_model=OntologyScanResponse)
async def scan_ontology_proposals(
    services: RequestServices = Depends(get_services),
) -> OntologyScanResponse | JSONResponse:
    try:
        created = await services.ontology.scan_and_propose(services.owner)
        return OntologyScanResponse(
            created_count=len(created),
            items=[_to_response(item) for item in created],
        )
    except DomainError as exc:
        return JSONResponse(
            status_code=400,
            content=domain_error_response(exc, services.correlation_id),
        )


@router.post("/ontology-proposals/{proposal_id}/approve", response_model=OntologyProposalResponse)
async def approve_ontology_proposal(
    proposal_id: UUID,
    body: OntologyDecisionRequest,
    services: RequestServices = Depends(get_services),
) -> OntologyProposalResponse | JSONResponse:
    try:
        proposal = await services.ontology.approve(
            services.owner,
            proposal_id,
            rationale=body.rationale,
        )
        return _to_response(proposal)
    except DomainError as exc:
        return JSONResponse(
            status_code=400,
            content=domain_error_response(exc, services.correlation_id),
        )


@router.post("/ontology-proposals/{proposal_id}/reject", response_model=OntologyProposalResponse)
async def reject_ontology_proposal(
    proposal_id: UUID,
    body: OntologyDecisionRequest,
    services: RequestServices = Depends(get_services),
) -> OntologyProposalResponse | JSONResponse:
    try:
        proposal = await services.ontology.reject(
            services.owner,
            proposal_id,
            rationale=body.rationale,
        )
        return _to_response(proposal)
    except DomainError as exc:
        return JSONResponse(
            status_code=400,
            content=domain_error_response(exc, services.correlation_id),
        )
