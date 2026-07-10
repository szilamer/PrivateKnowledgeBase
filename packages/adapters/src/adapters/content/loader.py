import base64
import os
from pathlib import Path
from uuid import UUID

import httpx


class LocalAndGitHubContentLoader:
    async def load(self, version_id: UUID, record: dict[str, object]) -> bytes:
        _ = version_id
        content_ref = str(record.get("content_ref") or "")
        if content_ref.startswith("github://"):
            return await self._load_github(content_ref, record)
        path = Path(content_ref).expanduser()
        if path.is_file():
            return path.read_bytes()
        msg = f"Cannot load content: {content_ref}"
        raise ValueError(msg)

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
