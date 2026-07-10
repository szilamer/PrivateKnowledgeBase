from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(request: Request) -> JSONResponse:
    checker = request.app.state.health_checker
    service = request.app.state.health_service
    dependencies = await checker.check_all()
    result = service.check(dependencies)
    status_code = 200 if result.status.value == "healthy" else 503
    return JSONResponse(status_code=status_code, content=result.model_dump())
