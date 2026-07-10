from uuid import uuid4

from adapters.connectors.google.oauth import GoogleOAuthService
from domain.errors import DomainError
from fastapi import APIRouter, Depends, Query, Request
from starlette.responses import JSONResponse, RedirectResponse

from api.dependencies import RequestServices, domain_error_response, get_google_oauth, get_services

router = APIRouter(tags=["google-connectors"])


@router.get("/connectors/google/auth-url", response_model=None)
async def google_auth_url(
    request: Request,
    oauth: GoogleOAuthService = Depends(get_google_oauth),
) -> dict[str, str] | JSONResponse:
    try:
        state = str(uuid4())
        request.app.state.google_oauth_states.add(state)
        return {"auth_url": oauth.build_auth_url(state=state)}
    except ValueError as exc:
        return JSONResponse(
            status_code=400,
            content={
                "code": "google_not_configured",
                "message": str(exc),
                "details": {},
                "correlation_id": str(uuid4()),
            },
        )


@router.get("/connectors/google/callback", response_model=None)
async def google_callback(
    request: Request,
    code: str = Query(...),
    state: str = Query(...),
    oauth: GoogleOAuthService = Depends(get_google_oauth),
) -> RedirectResponse | JSONResponse:
    states: set[str] = request.app.state.google_oauth_states
    if state not in states:
        return JSONResponse(status_code=400, content={"message": "Invalid OAuth state"})
    states.discard(state)
    try:
        await oauth.handle_callback(code=code)
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"message": str(exc)})
    return RedirectResponse(url="/sources/connect/google?connected=1")


@router.get("/connectors/google/accounts")
async def list_google_accounts(
    oauth: GoogleOAuthService = Depends(get_google_oauth),
) -> dict[str, object]:
    accounts = await oauth.list_accounts()
    return {"items": accounts}


@router.delete("/connectors/google/accounts/{account_alias}", response_model=None)
async def revoke_google_account(
    account_alias: str,
    services: RequestServices = Depends(get_services),
    oauth: GoogleOAuthService = Depends(get_google_oauth),
) -> dict[str, bool] | JSONResponse:
    try:
        revoked = await oauth.revoke_account(account_alias)
        return {"revoked": revoked}
    except ValueError as exc:
        return JSONResponse(
            status_code=400,
            content=domain_error_response(DomainError(str(exc)), services.correlation_id),
        )


@router.get("/connectors/google/drive/folders", response_model=None)
async def list_drive_folders(
    oauth: GoogleOAuthService = Depends(get_google_oauth),
    parent_id: str = Query(default="root"),
) -> dict[str, object] | JSONResponse:
    if not oauth.enabled:
        return JSONResponse(
            status_code=400,
            content={"message": "Google connectors not configured"},
        )
    import httpx

    token = await oauth.get_access_token("google:primary")
    query = (
        f"'{parent_id}' in parents and mimeType = 'application/vnd.google-apps.folder' "
        "and trashed = false"
    )
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            "https://www.googleapis.com/drive/v3/files",
            params={
                "q": query,
                "fields": "files(id,name)",
                "pageSize": 100,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        response.raise_for_status()
        payload = response.json()
    return {"items": payload.get("files", [])}


@router.get("/connectors/google/calendars", response_model=None)
async def list_calendars(
    oauth: GoogleOAuthService = Depends(get_google_oauth),
) -> dict[str, object] | JSONResponse:
    if not oauth.enabled:
        return JSONResponse(
            status_code=400,
            content={"message": "Google connectors not configured"},
        )
    import httpx

    token = await oauth.get_access_token("google:primary")
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            "https://www.googleapis.com/calendar/v3/users/me/calendarList",
            headers={"Authorization": f"Bearer {token}"},
        )
        response.raise_for_status()
        payload = response.json()
    return {"items": payload.get("items", [])}
