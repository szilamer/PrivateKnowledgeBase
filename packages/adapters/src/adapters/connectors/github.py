import base64
import os

import httpx
from domain.content_hash import compute_content_hash
from domain.sources import Source, SourceType
from domain.sync import DiscoveredObject


class GitHubConnector:
    """FR-SRC-002 — discover repository files via GitHub API."""

    ALLOWED_EXTENSIONS = {".md", ".txt", ".pdf"}

    async def discover(self, source: Source) -> list[DiscoveredObject]:
        if source.type != SourceType.GITHUB:
            msg = "Source is not a GitHub repository"
            raise ValueError(msg)

        owner = str(source.configuration.get("owner", ""))
        repo = str(source.configuration.get("repo", ""))
        branch = str(source.configuration.get("branch", "main"))
        token_env = str(source.configuration.get("token_env_var", "GITHUB_TOKEN"))
        token = os.environ.get(token_env)
        if not token:
            msg = f"GitHub token not found in environment: {token_env}"
            raise ValueError(msg)

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        api_base = "https://api.github.com"

        async with httpx.AsyncClient(timeout=30.0) as client:
            tree_resp = await client.get(
                f"{api_base}/repos/{owner}/{repo}/git/trees/{branch}",
                params={"recursive": "1"},
                headers=headers,
            )
            tree_resp.raise_for_status()
            tree = tree_resp.json()

            discovered: list[DiscoveredObject] = []
            for item in tree.get("tree", []):
                if item.get("type") != "blob":
                    continue
                path = item.get("path", "")
                if not any(path.lower().endswith(ext) for ext in self.ALLOWED_EXTENSIONS):
                    continue

                content_resp = await client.get(
                    f"{api_base}/repos/{owner}/{repo}/contents/{path}",
                    params={"ref": branch},
                    headers=headers,
                )
                if content_resp.status_code != 200:
                    continue
                payload = content_resp.json()
                if payload.get("encoding") != "base64":
                    continue
                raw = base64.b64decode(payload["content"])
                discovered.append(
                    DiscoveredObject(
                        external_id=path,
                        object_type="file",
                        content_hash=compute_content_hash(raw),
                        mime_type=None,
                        content_ref=f"github://{owner}/{repo}/{branch}/{path}",
                    )
                )
            return discovered
