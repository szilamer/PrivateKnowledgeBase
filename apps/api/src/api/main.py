from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from adapters.health import HealthChecker
from application.health import HealthService
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from observability.logging import configure_logging, get_logger
from starlette.responses import JSONResponse

from api.config import Settings
from api.routes.health import router as health_router

settings = Settings()
configure_logging(settings.log_level)
logger = get_logger("api")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.settings = settings
    app.state.health_checker = HealthChecker(settings)
    app.state.health_service = HealthService()
    logger.info("api_starting", app_env=settings.app_env)
    yield
    await app.state.health_checker.dispose()
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
