from application.sources.config_service import SourceConfigService
from domain.errors import DomainError
from domain.sync import SyncMode
from fastapi import APIRouter, Depends, Request
from starlette.responses import JSONResponse

from api.dependencies import RequestServices, domain_error_response, get_services
from api.schemas.source_config import (
    SourcesConfigPutRequest,
    SourcesConfigResponse,
    SourcesHealthResponse,
)

router = APIRouter(tags=["sources-config"])


def _config_service(request: Request) -> SourceConfigService:
    from pathlib import Path

    settings = request.app.state.settings
    return SourceConfigService(Path(settings.sources_config_path))


@router.get("/sources/config", response_model=SourcesConfigResponse)
async def get_sources_config(request: Request) -> SourcesConfigResponse:
    service = _config_service(request)
    return SourcesConfigResponse(
        config=service.get_config_redacted(),
        config_path=str(service.config_path),
    )


@router.put("/sources/config", response_model=SourcesConfigResponse)
async def put_sources_config(
    body: SourcesConfigPutRequest,
    request: Request,
    services: RequestServices = Depends(get_services),
) -> SourcesConfigResponse | JSONResponse:
    config_service = _config_service(request)
    try:
        config = config_service.put_config(body.config)
    except DomainError as exc:
        return JSONResponse(
            status_code=400,
            content=domain_error_response(exc, services.correlation_id),
        )

    upserted = await services.bootstrap.apply_config(config, correlation_id=services.correlation_id)
    if config.sync.on_startup:
        for source in upserted:
            if source.enabled:
                await services.sync.start_sync(
                    services.owner,
                    source.id,
                    SyncMode.INCREMENTAL,
                    correlation_id=services.correlation_id,
                    idempotency_key=f"config-put:{source.configuration.get('config_id')}",
                )

    return SourcesConfigResponse(
        config=config_service.get_config_redacted(),
        config_path=str(config_service.config_path),
    )


@router.get("/sources/health", response_model=SourcesHealthResponse)
async def sources_health(
    request: Request,
    services: RequestServices = Depends(get_services),
) -> SourcesHealthResponse:
    settings = request.app.state.settings
    config_service = _config_service(request)
    errors: list[str] = []
    config_loaded = config_service.config_path.is_file()
    source_count = 0
    try:
        items, _ = await services.sources.list_sources(services.owner, limit=100)
        source_count = len(items)
    except DomainError as exc:
        errors.append(str(exc))

    if config_loaded:
        try:
            config_service.get_config()
        except ValueError as exc:
            errors.append(str(exc))
            config_loaded = False

    status = "healthy" if not errors else "degraded"
    return SourcesHealthResponse(
        status=status,
        config_path=str(config_service.config_path),
        config_loaded=config_loaded,
        source_count=source_count,
        errors=errors,
        google_connectors_enabled=settings.pkb_google_connectors_enabled,
    )
