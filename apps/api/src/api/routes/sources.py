from uuid import UUID

from application.sources.browse_service import LocalFolderBrowseService
from domain.errors import DomainError
from domain.sources import RegisterGitHubSourceCommand, RegisterLocalSourceCommand
from fastapi import APIRouter, Depends, Query, Request
from starlette.responses import JSONResponse

from api.dependencies import RequestServices, domain_error_response, get_services
from api.schemas.local_browse import LocalBrowseResponse, LocalFolderEntryResponse
from api.schemas.sources import (
    GitHubSourceRequest,
    LocalSourceRequest,
    SourceListResponse,
    SourceResponse,
)

router = APIRouter(tags=["sources"])


def _browse_service(request: Request) -> LocalFolderBrowseService:
    settings = request.app.state.settings
    return LocalFolderBrowseService(host_root=settings.pkb_host_root)


@router.get("/sources/local/browse", response_model=LocalBrowseResponse)
async def browse_local_folders(
    request: Request,
    path: str = Query(default="~"),
) -> LocalBrowseResponse:
    result = _browse_service(request).browse(path)
    return LocalBrowseResponse(
        path=result.path,
        parent_path=result.parent_path,
        entries=[
            LocalFolderEntryResponse(
                name=entry.name,
                path=entry.path,
                has_children=entry.has_children,
            )
            for entry in result.entries
        ],
        can_select=result.can_select,
        readable=result.readable,
        error=result.error,
    )


def _to_response(source: object) -> SourceResponse:
    from domain.sources import Source

    assert isinstance(source, Source)
    return SourceResponse(
        id=source.id,
        type=source.type,
        name=source.name,
        owner_id=source.owner_id,
        configuration=source.configuration,
        enabled=source.enabled,
        default_project_id=source.default_project_id,
    )


@router.get("/sources", response_model=SourceListResponse)
async def list_sources(
    services: RequestServices = Depends(get_services),
    limit: int = Query(default=50, ge=1, le=100),
    cursor: UUID | None = Query(default=None),
) -> SourceListResponse | JSONResponse:
    try:
        items, next_cursor = await services.sources.list_sources(
            services.owner, limit=limit, cursor=cursor
        )
        return SourceListResponse(
            items=[_to_response(item) for item in items],
            next_cursor=next_cursor,
        )
    except DomainError as exc:
        return JSONResponse(
            status_code=403,
            content=domain_error_response(exc, services.correlation_id),
        )


@router.get("/sources/{source_id}", response_model=SourceResponse)
async def get_source(
    source_id: UUID,
    services: RequestServices = Depends(get_services),
) -> SourceResponse | JSONResponse:
    try:
        source = await services.sources.get_source(services.owner, source_id)
        return _to_response(source)
    except DomainError as exc:
        return JSONResponse(
            status_code=404,
            content=domain_error_response(exc, services.correlation_id),
        )


@router.post("/sources/local", response_model=SourceResponse, status_code=201)
async def register_local_source(
    body: LocalSourceRequest,
    request: Request,
    services: RequestServices = Depends(get_services),
) -> SourceResponse | JSONResponse:
    try:
        browse = _browse_service(request)
        candidate_paths = list(body.paths)
        if body.path.strip():
            candidate_paths.append(body.path.strip())
        for folder_path in candidate_paths:
            browse.validate_selectable(folder_path)
        source = await services.sources.register_local(
            services.owner,
            RegisterLocalSourceCommand(**body.model_dump()),
            correlation_id=services.correlation_id,
        )
        return _to_response(source)
    except DomainError as exc:
        return JSONResponse(
            status_code=400,
            content=domain_error_response(exc, services.correlation_id),
        )


@router.post("/sources/github", response_model=SourceResponse, status_code=201)
async def register_github_source(
    body: GitHubSourceRequest,
    services: RequestServices = Depends(get_services),
) -> SourceResponse | JSONResponse:
    try:
        source = await services.sources.register_github(
            services.owner,
            RegisterGitHubSourceCommand(**body.model_dump()),
            correlation_id=services.correlation_id,
        )
        return _to_response(source)
    except DomainError as exc:
        return JSONResponse(
            status_code=400,
            content=domain_error_response(exc, services.correlation_id),
        )
