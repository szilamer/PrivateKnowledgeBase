from __future__ import annotations

import httpx
from adapters.connectors.google.oauth import (
    GoogleOAuthService,
    content_hash_from_parts,
)
from domain.sources import Source, SourceType
from domain.sync import DiscoveredObject


class GoogleDriveConnector:
    """FR-SRC-013 — discover files in selected Drive folders."""

    def __init__(self, oauth: GoogleOAuthService) -> None:
        self._oauth = oauth

    async def discover(self, source: Source) -> list[DiscoveredObject]:
        if source.type != SourceType.GOOGLE_DRIVE:
            msg = "Source is not Google Drive"
            raise ValueError(msg)
        if not self._oauth.enabled:
            return []

        account = str(source.configuration.get("account", "google:primary"))
        folder_ids = source.configuration.get("folder_ids", [])
        if not isinstance(folder_ids, list) or not folder_ids:
            return []

        include_google_docs = bool(source.configuration.get("include_google_docs", True))
        raw_extensions = source.configuration.get("include_extensions", [".md", ".txt", ".pdf"])
        extensions = (
            {str(ext).lower() for ext in raw_extensions}
            if isinstance(raw_extensions, list)
            else {".md", ".txt", ".pdf"}
        )

        token = await self._oauth.get_access_token(account)
        discovered: list[DiscoveredObject] = []
        async with httpx.AsyncClient(timeout=60.0) as client:
            for folder_id in folder_ids:
                query = f"'{folder_id}' in parents and trashed = false"
                page_token: str | None = None
                while True:
                    params: dict[str, str | int] = {
                        "q": query,
                        "fields": (
                            "nextPageToken,files(id,name,mimeType,modifiedTime,md5Checksum)"
                        ),
                        "pageSize": 200,
                    }
                    if page_token:
                        params["pageToken"] = page_token
                    response = await client.get(
                        "https://www.googleapis.com/drive/v3/files",
                        params=params,
                        headers={"Authorization": f"Bearer {token}"},
                    )
                    response.raise_for_status()
                    payload = response.json()
                    for item in payload.get("files", []):
                        discovered.append(_file_to_object(item, include_google_docs, extensions))
                    page_token = payload.get("nextPageToken")
                    if not page_token:
                        break
        return discovered


def _file_to_object(
    item: dict[str, object],
    include_google_docs: bool,
    extensions: set[str],
) -> DiscoveredObject:
    file_id = str(item["id"])
    name = str(item.get("name", file_id))
    mime_type = str(item.get("mimeType", "application/octet-stream"))
    modified = str(item.get("modifiedTime", ""))
    md5 = str(item.get("md5Checksum", ""))

    if mime_type == "application/vnd.google-apps.document":
        if not include_google_docs:
            return DiscoveredObject(
                external_id=file_id,
                object_type="file",
                content_hash=content_hash_from_parts(file_id, modified),
                mime_type=mime_type,
                content_ref=f"google://drive/{file_id}/export?mime=text/plain",
            )
        content_ref = f"google://drive/{file_id}/export?mime=text/plain"
        return DiscoveredObject(
            external_id=file_id,
            object_type="file",
            content_hash=content_hash_from_parts(file_id, modified, "gdoc"),
            mime_type="text/plain",
            content_ref=content_ref,
        )

    if not any(name.lower().endswith(ext) for ext in extensions):
        return DiscoveredObject(
            external_id=file_id,
            object_type="file",
            content_hash=content_hash_from_parts(file_id, modified, md5),
            mime_type=mime_type,
            content_ref=f"google://drive/{file_id}",
        )

    return DiscoveredObject(
        external_id=file_id,
        object_type="file",
        content_hash=content_hash_from_parts(file_id, modified, md5),
        mime_type=mime_type,
        content_ref=f"google://drive/{file_id}",
    )
