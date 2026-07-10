from __future__ import annotations

import base64

import httpx
from adapters.connectors.google.oauth import (
    GoogleOAuthService,
    content_hash_from_parts,
    inline_content_ref,
)
from domain.sources import Source, SourceType
from domain.sync import DiscoveredObject


class GmailConnector:
    """FR-SRC-014 — discover Gmail messages matching scope."""

    def __init__(self, oauth: GoogleOAuthService) -> None:
        self._oauth = oauth

    async def discover(self, source: Source) -> list[DiscoveredObject]:
        if source.type != SourceType.GMAIL:
            msg = "Source is not Gmail"
            raise ValueError(msg)
        if not self._oauth.enabled:
            return []

        account = str(source.configuration.get("account", "google:primary"))
        query = str(source.configuration.get("query", "label:important newer_than:365d"))
        token = await self._oauth.get_access_token(account)
        discovered: list[DiscoveredObject] = []

        async with httpx.AsyncClient(timeout=60.0) as client:
            page_token: str | None = None
            while True:
                params: dict[str, str | int] = {"q": query, "maxResults": 100}
                if page_token:
                    params["pageToken"] = page_token
                list_response = await client.get(
                    "https://gmail.googleapis.com/gmail/v1/users/me/messages",
                    params=params,
                    headers={"Authorization": f"Bearer {token}"},
                )
                list_response.raise_for_status()
                payload = list_response.json()
                for summary in payload.get("messages", []):
                    message_id = str(summary["id"])
                    message_response = await client.get(
                        f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{message_id}",
                        params={"format": "full"},
                        headers={"Authorization": f"Bearer {token}"},
                    )
                    message_response.raise_for_status()
                    message = message_response.json()
                    discovered.append(_message_to_object(message))
                page_token = payload.get("nextPageToken")
                if not page_token:
                    break
        return discovered


def _message_to_object(message: dict[str, object]) -> DiscoveredObject:
    message_id = str(message["id"])
    headers = _headers_map(message)
    subject = headers.get("Subject", "(no subject)")
    from_addr = headers.get("From", "")
    body_text = _extract_body(message)
    text = f"Subject: {subject}\nFrom: {from_addr}\n\n{body_text}".strip()
    return DiscoveredObject(
        external_id=message_id,
        object_type="email",
        content_hash=content_hash_from_parts(message_id, str(message.get("historyId", ""))),
        mime_type="message/rfc822",
        content_ref=inline_content_ref(text.encode("utf-8")),
    )


def _headers_map(message: dict[str, object]) -> dict[str, str]:
    payload = message.get("payload")
    if not isinstance(payload, dict):
        return {}
    headers = payload.get("headers", [])
    if not isinstance(headers, list):
        return {}
    result: dict[str, str] = {}
    for item in headers:
        if isinstance(item, dict):
            name = str(item.get("name", ""))
            value = str(item.get("value", ""))
            if name:
                result[name] = value
    return result


def _extract_body(message: dict[str, object]) -> str:
    payload = message.get("payload")
    if not isinstance(payload, dict):
        return ""
    parts = [payload]
    texts: list[str] = []
    while parts:
        part = parts.pop()
        if not isinstance(part, dict):
            continue
        mime_type = str(part.get("mimeType", ""))
        body = part.get("body")
        if isinstance(body, dict) and body.get("data"):
            decoded = base64.urlsafe_b64decode(str(body["data"]) + "==")
            if mime_type.startswith("text/"):
                texts.append(decoded.decode("utf-8", errors="replace"))
        nested = part.get("parts")
        if isinstance(nested, list):
            parts.extend(nested)
    return "\n".join(texts).strip()
