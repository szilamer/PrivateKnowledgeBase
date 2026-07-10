from uuid import UUID

from domain.errors import DomainError
from fastapi import APIRouter, Depends, Query
from starlette.responses import JSONResponse

from api.dependencies import RequestServices, domain_error_response, get_services
from api.schemas.canonical import (
    ClaimListResponse,
    ClaimResponse,
    ContradictionListResponse,
    ContradictionResponse,
    EntityListResponse,
    EntityResponse,
    GraphEdgeResponse,
    GraphNodeResponse,
    GraphViewResponse,
    ProvenanceResponse,
)

router = APIRouter(tags=["canonical"])


def _entity_response(entity: object) -> EntityResponse:
    from domain.canonical import CanonicalEntity

    assert isinstance(entity, CanonicalEntity)
    return EntityResponse(
        id=entity.id,
        entity_type=entity.entity_type.value,
        canonical_name=entity.canonical_name,
        aliases=entity.aliases,
        description=entity.description,
        status=entity.status,
        source_proposal_id=entity.source_proposal_id,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


def _claim_response(claim: object) -> ClaimResponse:
    from domain.canonical import CanonicalClaim

    assert isinstance(claim, CanonicalClaim)
    return ClaimResponse(
        id=claim.id,
        subject_entity_id=claim.subject_entity_id,
        predicate=claim.predicate,
        object_value=claim.object_value,
        status=claim.status.value,
        confidence=claim.confidence,
        valid_from=claim.valid_from,
        valid_to=claim.valid_to,
        source_proposal_id=claim.source_proposal_id,
        provenance=[
            ProvenanceResponse(
                id=item.id,
                source_object_version_id=item.source_object_version_id,
                content_chunk_id=item.content_chunk_id,
                proposal_id=item.proposal_id,
                confidence=item.confidence,
            )
            for item in claim.provenance
        ],
        created_at=claim.created_at,
        updated_at=claim.updated_at,
    )


@router.get("/entities", response_model=EntityListResponse)
async def list_entities(
    services: RequestServices = Depends(get_services),
    limit: int = Query(default=50, ge=1, le=100),
    cursor: UUID | None = Query(default=None),
) -> EntityListResponse | JSONResponse:
    try:
        items, next_cursor = await services.canonical.list_entities(
            services.owner, limit=limit, cursor=cursor
        )
        return EntityListResponse(
            items=[_entity_response(item) for item in items],
            next_cursor=next_cursor,
        )
    except DomainError as exc:
        return JSONResponse(
            status_code=403,
            content=domain_error_response(exc, services.correlation_id),
        )


@router.get("/entities/{entity_id}", response_model=EntityResponse)
async def get_entity(
    entity_id: UUID,
    services: RequestServices = Depends(get_services),
) -> EntityResponse | JSONResponse:
    entity = await services.canonical.get_entity(services.owner, entity_id)
    if entity is None:
        return JSONResponse(
            status_code=404,
            content={
                "code": "not_found",
                "message": "Entity not found",
                "details": {},
                "correlation_id": services.correlation_id,
            },
        )
    return _entity_response(entity)


@router.get("/claims", response_model=ClaimListResponse)
async def list_claims(
    services: RequestServices = Depends(get_services),
    status: str | None = Query(default="active"),
    limit: int = Query(default=50, ge=1, le=100),
    cursor: UUID | None = Query(default=None),
) -> ClaimListResponse | JSONResponse:
    items, next_cursor = await services.canonical.list_claims(
        services.owner, limit=limit, cursor=cursor, status=status
    )
    return ClaimListResponse(
        items=[_claim_response(item) for item in items],
        next_cursor=next_cursor,
    )


@router.get("/claims/{claim_id}", response_model=ClaimResponse)
async def get_claim(
    claim_id: UUID,
    services: RequestServices = Depends(get_services),
) -> ClaimResponse | JSONResponse:
    claim = await services.canonical.get_claim(services.owner, claim_id)
    if claim is None:
        return JSONResponse(
            status_code=404,
            content={
                "code": "not_found",
                "message": "Claim not found",
                "details": {},
                "correlation_id": services.correlation_id,
            },
        )
    return _claim_response(claim)


@router.get("/contradictions", response_model=ContradictionListResponse)
async def list_contradictions(
    services: RequestServices = Depends(get_services),
    status: str | None = Query(default="open"),
    limit: int = Query(default=50, ge=1, le=100),
) -> ContradictionListResponse:
    items = await services.canonical.list_contradictions(services.owner, status=status, limit=limit)
    return ContradictionListResponse(
        items=[
            ContradictionResponse(
                id=item.id,
                existing_claim_id=item.existing_claim_id,
                conflicting_claim_id=item.conflicting_claim_id,
                conflicting_proposal_id=item.conflicting_proposal_id,
                status=item.status.value,
                summary=item.summary,
                created_at=item.created_at,
            )
            for item in items
        ]
    )


@router.get("/graph/neighborhood/{entity_id}", response_model=GraphViewResponse)
async def graph_neighborhood(
    entity_id: UUID,
    services: RequestServices = Depends(get_services),
    depth: int = Query(default=1, ge=1, le=3),
    limit: int = Query(default=50, ge=1, le=200),
) -> GraphViewResponse | JSONResponse:
    try:
        view = await services.graph.neighborhood(
            services.owner, entity_id, depth=depth, limit=limit
        )
        return GraphViewResponse(
            root_id=view.root_id,
            depth=view.depth,
            nodes=[
                GraphNodeResponse(
                    id=node.id,
                    label=node.label,
                    node_type=node.node_type,
                    properties=node.properties,
                )
                for node in view.nodes
            ],
            edges=[
                GraphEdgeResponse(
                    id=edge.id,
                    source_id=edge.source_id,
                    target_id=edge.target_id,
                    edge_type=edge.edge_type,
                    properties=edge.properties,
                )
                for edge in view.edges
            ],
            truncated=view.truncated,
        )
    except DomainError as exc:
        return JSONResponse(
            status_code=403,
            content=domain_error_response(exc, services.correlation_id),
        )


@router.get("/graph/subgraph", response_model=GraphViewResponse)
async def graph_subgraph(
    services: RequestServices = Depends(get_services),
    root_entity_id: UUID | None = Query(default=None),
    depth: int = Query(default=2, ge=1, le=3),
    limit: int = Query(default=100, ge=1, le=200),
) -> GraphViewResponse | JSONResponse:
    try:
        view = await services.graph.subgraph(
            services.owner,
            root_entity_id=root_entity_id,
            depth=depth,
            limit=limit,
        )
        return GraphViewResponse(
            root_id=view.root_id,
            depth=view.depth,
            nodes=[
                GraphNodeResponse(
                    id=node.id,
                    label=node.label,
                    node_type=node.node_type,
                    properties=node.properties,
                )
                for node in view.nodes
            ],
            edges=[
                GraphEdgeResponse(
                    id=edge.id,
                    source_id=edge.source_id,
                    target_id=edge.target_id,
                    edge_type=edge.edge_type,
                    properties=edge.properties,
                )
                for edge in view.edges
            ],
            truncated=view.truncated,
        )
    except DomainError as exc:
        return JSONResponse(
            status_code=403,
            content=domain_error_response(exc, services.correlation_id),
        )
