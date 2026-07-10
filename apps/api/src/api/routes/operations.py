from adapters.graph.projector import Neo4jGraphProjector
from domain.errors import DomainError
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse

from api.dependencies import RequestServices, domain_error_response, get_services
from api.schemas.operations import (
    OperationsStatusResponse,
    ProjectionRebuildAcceptedResponse,
    ProjectionRebuildResponse,
)

router = APIRouter(tags=["operations"])


@router.get("/operations/status", response_model=OperationsStatusResponse)
async def operations_status(
    services: RequestServices = Depends(get_services),
) -> OperationsStatusResponse:
    status = await services.operations.get_status(services.owner)
    return OperationsStatusResponse(
        pending_outbox_events=status.pending_outbox_events,
        failed_outbox_events=status.failed_outbox_events,
        processed_outbox_events=status.processed_outbox_events,
        canonical_entities=status.canonical_entities,
        canonical_claims=status.canonical_claims,
        projection_rebuild_recommended=status.projection_rebuild_recommended,
    )


@router.post(
    "/operations/projection/rebuild",
    response_model=ProjectionRebuildResponse | ProjectionRebuildAcceptedResponse,
)
async def rebuild_projection(
    request: Request,
    services: RequestServices = Depends(get_services),
    async_mode: bool = Query(default=False, alias="async"),
) -> ProjectionRebuildResponse | ProjectionRebuildAcceptedResponse | JSONResponse:
    if async_mode:
        await services.tasks.enqueue_projection_rebuild(services.owner.owner_id)
        return ProjectionRebuildAcceptedResponse(
            status="accepted",
            task="worker.tasks.maintenance.rebuild_projection",
        )

    settings = request.app.state.settings
    projector = Neo4jGraphProjector(settings)
    try:
        try:
            result = await services.operations.rebuild_projection(services.owner, projector)
        except DomainError as exc:
            return JSONResponse(
                status_code=403,
                content=domain_error_response(exc, services.correlation_id),
            )
    finally:
        await projector.close()

    return ProjectionRebuildResponse(
        entities_projected=result.entities_projected,
        relationships_projected=result.relationships_projected,
        claims_projected=result.claims_projected,
        contradictions_projected=result.contradictions_projected,
        cleared_nodes=result.cleared_nodes,
    )
