from uuid import UUID

from domain.errors import DomainError
from fastapi import APIRouter, Depends, Header, Query
from starlette.responses import JSONResponse

from api.dependencies import RequestServices, domain_error_response, get_services
from api.schemas.sources import StartSyncRequest, SyncRunListResponse, SyncRunResponse

router = APIRouter(tags=["sync-runs"])


def _to_response(sync_run: object) -> SyncRunResponse:
    from domain.sync import SyncRun

    assert isinstance(sync_run, SyncRun)
    return SyncRunResponse(
        id=sync_run.id,
        source_id=sync_run.source_id,
        mode=sync_run.mode,
        status=sync_run.status,
        correlation_id=sync_run.correlation_id,
        objects_discovered=sync_run.objects_discovered,
        objects_processed=sync_run.objects_processed,
        objects_failed=sync_run.objects_failed,
        error_summary=sync_run.error_summary,
        started_at=sync_run.started_at,
        completed_at=sync_run.completed_at,
    )


@router.post("/sync-runs", response_model=SyncRunResponse, status_code=202)
async def start_sync(
    body: StartSyncRequest,
    services: RequestServices = Depends(get_services),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> SyncRunResponse | JSONResponse:
    try:
        sync_run = await services.sync.start_sync(
            services.owner,
            body.source_id,
            body.mode,
            correlation_id=services.correlation_id,
            idempotency_key=idempotency_key,
        )
        return _to_response(sync_run)
    except DomainError as exc:
        return JSONResponse(
            status_code=400,
            content=domain_error_response(exc, services.correlation_id),
        )


@router.get("/sync-runs/{sync_run_id}", response_model=SyncRunResponse)
async def get_sync_run(
    sync_run_id: UUID,
    services: RequestServices = Depends(get_services),
) -> SyncRunResponse | JSONResponse:
    try:
        sync_run = await services.sync.get_sync_run(services.owner, sync_run_id)
        return _to_response(sync_run)
    except DomainError as exc:
        return JSONResponse(
            status_code=404,
            content=domain_error_response(exc, services.correlation_id),
        )


@router.get("/sources/{source_id}/sync-runs", response_model=SyncRunListResponse)
async def list_sync_runs(
    source_id: UUID,
    services: RequestServices = Depends(get_services),
    limit: int = Query(default=50, ge=1, le=100),
    cursor: UUID | None = Query(default=None),
) -> SyncRunListResponse | JSONResponse:
    try:
        items, next_cursor = await services.sync.list_sync_runs(
            services.owner, source_id, limit=limit, cursor=cursor
        )
        return SyncRunListResponse(
            items=[_to_response(item) for item in items],
            next_cursor=next_cursor,
        )
    except DomainError as exc:
        return JSONResponse(
            status_code=404,
            content=domain_error_response(exc, services.correlation_id),
        )
