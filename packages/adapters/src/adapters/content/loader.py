import base64
import os
from pathlib import Path
from uuid import UUID

import httpx
from adapters.connectors.google.oauth import GoogleOAuthService


class LocalAndGitHubContentLoader:
    def __init__(self, oauth_service: GoogleOAuthService | None = None) -> None:
        self._oauth = oauth_service

    async def load(self, version_id: UUID, record: dict[str, object]) -> bytes:
        _ = version_id
        content_ref = str(record.get("content_ref") or "")
        if content_ref.startswith("inline:"):
            return base64.b64decode(content_ref.removeprefix("inline:"))
        if content_ref.startswith("google://"):
            return await self._load_google(content_ref)
        if content_ref.startswith("github://"):
            return await self._load_github(content_ref, record)
        path = Path(content_ref).expanduser()
        if path.is_file():
            return path.read_bytes()
        msg = f"Cannot load content: {content_ref}"
        raise ValueError(msg)

    async def _load_google(self, content_ref: str) -> bytes:
        if self._oauth is None or not self._oauth.enabled:
            raise ValueError("Google connectors are not enabled")

        remainder = content_ref.removeprefix("google://")
        if remainder.startswith("drive/"):
            return await self._load_drive(remainder.removeprefix("drive/"), self._oauth)
        msg = f"Unsupported google content ref: {content_ref}"
        raise ValueError(msg)

    async def _load_drive(self, ref: str, oauth: GoogleOAuthService) -> bytes:
        token = await oauth.get_access_token("google:primary")
        if "/export?" in ref:
            file_id, query = ref.split("/export?", 1)
            params = dict(item.split("=", 1) for item in query.split("&") if "=" in item)
            mime = params.get("mime", "text/plain")
            url = f"https://www.googleapis.com/drive/v3/files/{file_id}/export"
            request_params = {"mimeType": mime}
        else:
            file_id = ref
            url = f"https://www.googleapis.com/drive/v3/files/{file_id}"
            request_params = {"alt": "media"}

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(
                url,
                params=request_params,
                headers={"Authorization": f"Bearer {token}"},
            )
            response.raise_for_status()
            return response.content

    async def _load_github(self, content_ref: str, record: dict[str, object]) -> bytes:
        parts = content_ref.removeprefix("github://").split("/", 3)
        if len(parts) < 4:
            raise ValueError(f"Invalid github content ref: {content_ref}")
        owner, repo, branch, path = parts
        config = record.get("configuration") or {}
        if not isinstance(config, dict):
            config = {}
        token_env = str(config.get("token_env_var", "GITHUB_TOKEN"))
        token = os.environ.get(token_env, "")
        if not token:
            raise ValueError(f"GitHub token not found: {token_env}")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"https://api.github.com/repos/{owner}/{repo}/contents/{path}",
                params={"ref": branch},
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json",
                },
            )
            response.raise_for_status()
            payload = response.json()
            return base64.b64decode(payload["content"])
