from uuid import UUID

from domain.content import SearchRequest
from domain.errors import DomainError
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from starlette.responses import JSONResponse

from api.dependencies import RequestServices, domain_error_response, get_services
from api.schemas.content import SearchHitResponse, SearchResultResponse

router = APIRouter(tags=["search"])


class SearchBody(BaseModel):
    query: str
    mode: str = "hybrid"
    limit: int = Field(default=20, ge=1, le=100)


@router.post("/search", response_model=SearchResultResponse)
async def search(
    body: SearchBody,
    services: RequestServices = Depends(get_services),
) -> SearchResultResponse:
    result = await services.search.search(
        services.owner,
        SearchRequest(query=body.query, mode=body.mode, limit=body.limit),
    )
    return SearchResultResponse(
        query=result.query,
        mode=result.mode,
        hits=[
            SearchHitResponse(
                chunk_id=hit.chunk_id,
                source_id=hit.source_id,
                source_object_version_id=hit.source_object_version_id,
                external_id=hit.external_id,
                text=hit.text,
                score=hit.score,
                match_type=hit.match_type,
                anchor_start=hit.anchor_start,
                anchor_end=hit.anchor_end,
            )
            for hit in result.hits
        ],
    )


@router.get("/source-objects/versions/{version_id}/preview")
async def preview_source_version(
    version_id: UUID,
    services: RequestServices = Depends(get_services),
) -> JSONResponse:
    try:
        preview = await services.preview.get_preview(services.owner, version_id)
        return JSONResponse(content=preview.model_dump(mode="json"))
    except DomainError as exc:
        return JSONResponse(
            status_code=404,
            content=domain_error_response(exc, services.correlation_id),
        )
