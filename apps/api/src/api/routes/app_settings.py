from pathlib import Path

import httpx
from application.settings.service import AppSettingsService
from domain.errors import DomainError
from fastapi import APIRouter, Depends, Request
from starlette.responses import JSONResponse

from api.dependencies import RequestServices, domain_error_response, get_services
from api.schemas.app_settings import (
    AppSettingsPutRequest,
    AppSettingsResponse,
    LlmHealthResponse,
)

router = APIRouter(tags=["settings"])


def _settings_service(request: Request) -> AppSettingsService:
    settings = request.app.state.settings
    return AppSettingsService(Path(settings.settings_config_path), settings)


@router.get("/settings", response_model=AppSettingsResponse)
async def get_settings(request: Request) -> AppSettingsResponse:
    service = _settings_service(request)
    return AppSettingsResponse(
        config=service.get_config_redacted(),
        config_path=str(service.config_path),
    )


@router.put("/settings", response_model=AppSettingsResponse)
async def put_settings(
    body: AppSettingsPutRequest,
    request: Request,
    services: RequestServices = Depends(get_services),
) -> AppSettingsResponse | JSONResponse:
    service = _settings_service(request)
    try:
        service.put_config(body.config)
    except DomainError as exc:
        return JSONResponse(
            status_code=400,
            content=domain_error_response(exc, services.correlation_id),
        )
    request.app.state.resolved_llm_settings = service.get_resolved()
    return AppSettingsResponse(
        config=service.get_config_redacted(),
        config_path=str(service.config_path),
    )


@router.get("/settings/llm/health", response_model=LlmHealthResponse)
async def llm_health(request: Request) -> LlmHealthResponse:
    service = _settings_service(request)
    resolved = service.get_resolved()
    if not resolved.llm_enabled:
        return LlmHealthResponse(
            status="disabled",
            llm_enabled=False,
            api_key_configured=resolved.api_key_configured,
            base_url=resolved.llm_base_url,
            extraction_model=resolved.extraction_model,
            synthesis_model=resolved.synthesis_model,
            embedding_provider="hash" if resolved.use_hash_embeddings else "api",
            message="LLM kikapcsolva a beállításokban.",
        )

    embedding_provider = "hash" if resolved.use_hash_embeddings else "api"
    if resolved.use_hash_embeddings:
        return LlmHealthResponse(
            status="offline",
            llm_enabled=True,
            api_key_configured=resolved.api_key_configured,
            base_url=resolved.llm_base_url,
            extraction_model=resolved.extraction_model,
            synthesis_model=resolved.synthesis_model,
            embedding_provider=embedding_provider,
            message="Offline mód: hash embedding és heurisztikus kivonás.",
        )

    try:
        headers: dict[str, str] = {}
        if resolved.llm_api_key:
            headers["Authorization"] = f"Bearer {resolved.llm_api_key}"
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.get(
                f"{resolved.llm_base_url.rstrip('/')}/models",
                headers=headers,
            )
            if response.status_code < 500:
                return LlmHealthResponse(
                    status="healthy",
                    llm_enabled=True,
                    api_key_configured=True,
                    base_url=resolved.llm_base_url,
                    extraction_model=resolved.extraction_model,
                    synthesis_model=resolved.synthesis_model,
                    embedding_provider=embedding_provider,
                    message="LLM szolgáltatás elérhető.",
                )
    except Exception as exc:  # noqa: BLE001
        return LlmHealthResponse(
            status="unreachable",
            llm_enabled=True,
            api_key_configured=resolved.api_key_configured,
            base_url=resolved.llm_base_url,
            extraction_model=resolved.extraction_model,
            synthesis_model=resolved.synthesis_model,
            embedding_provider=embedding_provider,
            message=f"LLM nem elérhető: {exc}",
        )

    return LlmHealthResponse(
        status="degraded",
        llm_enabled=True,
        api_key_configured=resolved.api_key_configured,
        base_url=resolved.llm_base_url,
        extraction_model=resolved.extraction_model,
        synthesis_model=resolved.synthesis_model,
        embedding_provider=embedding_provider,
        message="LLM válasz nem egyértelmű.",
    )
