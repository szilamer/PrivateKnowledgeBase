from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from adapters.health import HealthChecker
from adapters.persistence.session import create_engine, create_session_factory
from adapters.sources.host_path_bridge import HostPathBridge
from application.health import HealthService
from application.settings.service import AppSettingsService
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from observability.logging import configure_logging, get_logger
from starlette.responses import JSONResponse

from api.bootstrap import bootstrap_sources
from api.config import Settings
from api.routes.app_settings import router as app_settings_router
from api.routes.canonical import router as canonical_router
from api.routes.google_connectors import router as google_connectors_router
from api.routes.health import router as health_router
from api.routes.operations import router as operations_router
from api.routes.projects import router as projects_router
from api.routes.proposals import router as proposals_router
from api.routes.questions import router as questions_router
from api.routes.search import router as search_router
from api.routes.source_config import router as source_config_router
from api.routes.sources import router as sources_router
from api.routes.sync_runs import router as sync_runs_router

settings = Settings()
configure_logging(settings.log_level)
logger = get_logger("api")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.settings = settings
    app.state.health_checker = HealthChecker(settings)
    app.state.health_service = HealthService()
    engine = create_engine(settings.database_url)
    app.state.session_factory = create_session_factory(engine)
    app.state.db_engine = engine
    app.state.path_bridge = HostPathBridge(
        Path(settings.host_path_manifest_path),
        host_root=settings.pkb_host_root,
    )
    app.state.resolved_llm_settings = AppSettingsService(
        Path(settings.settings_config_path),
        settings,
        Path(settings.llm_secrets_path),
    ).get_resolved()
    oauth_states: set[str] = set()
    app.state.google_oauth_states = oauth_states
    logger.info("api_starting", app_env=settings.app_env)
    if settings.sources_bootstrap_on_startup:
        await bootstrap_sources(app)
    yield
    await app.state.health_checker.dispose()
    await app.state.db_engine.dispose()
    logger.info("api_stopped")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Private Knowledge Base API",
        version="0.1.0",
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        correlation_id = request.headers.get("X-Correlation-ID", "unknown")
        logger.error("unhandled_exception", correlation_id=correlation_id, error=str(exc))
        return JSONResponse(
            status_code=500,
            content={
                "code": "internal_error",
                "message": "An unexpected error occurred.",
                "details": {},
                "correlation_id": correlation_id,
            },
        )

    app.include_router(health_router, prefix="/api/v1")
    app.include_router(sources_router, prefix="/api/v1")
    app.include_router(source_config_router, prefix="/api/v1")
    app.include_router(google_connectors_router, prefix="/api/v1")
    app.include_router(app_settings_router, prefix="/api/v1")
    app.include_router(sync_runs_router, prefix="/api/v1")
    app.include_router(search_router, prefix="/api/v1")
    app.include_router(proposals_router, prefix="/api/v1")
    app.include_router(canonical_router, prefix="/api/v1")
    app.include_router(questions_router, prefix="/api/v1")
    app.include_router(projects_router, prefix="/api/v1")
    app.include_router(operations_router, prefix="/api/v1")
    return app


app = create_app()


def run() -> None:
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.app_env == "development",
    )


if __name__ == "__main__":
    run()
