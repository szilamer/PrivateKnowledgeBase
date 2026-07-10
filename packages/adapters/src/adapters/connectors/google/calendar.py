from __future__ import annotations

from datetime import UTC, datetime, timedelta

import httpx
from adapters.connectors.google.oauth import (
    GoogleOAuthService,
    content_hash_from_parts,
    inline_content_ref,
)
from domain.sources import Source, SourceType
from domain.sync import DiscoveredObject


class GoogleCalendarConnector:
    """FR-SRC-015 — discover calendar events within configured horizon."""

    def __init__(self, oauth: GoogleOAuthService) -> None:
        self._oauth = oauth

    async def discover(self, source: Source) -> list[DiscoveredObject]:
        if source.type != SourceType.GOOGLE_CALENDAR:
            msg = "Source is not Google Calendar"
            raise ValueError(msg)
        if not self._oauth.enabled:
            return []

        account = str(source.configuration.get("account", "google:primary"))
        calendar_ids = source.configuration.get("calendar_ids", ["primary"])
        if not isinstance(calendar_ids, list):
            calendar_ids = ["primary"]
        past_days = int(str(source.configuration.get("horizon_past_days", 365)))
        future_days = int(str(source.configuration.get("horizon_future_days", 90)))

        now = datetime.now(UTC)
        time_min = (now - timedelta(days=past_days)).isoformat()
        time_max = (now + timedelta(days=future_days)).isoformat()
        token = await self._oauth.get_access_token(account)
        discovered: list[DiscoveredObject] = []

        async with httpx.AsyncClient(timeout=60.0) as client:
            for calendar_id in calendar_ids:
                page_token: str | None = None
                while True:
                    params: dict[str, str | int | bool] = {
                        "timeMin": time_min,
                        "timeMax": time_max,
                        "singleEvents": True,
                        "orderBy": "startTime",
                        "maxResults": 250,
                    }
                    if page_token:
                        params["pageToken"] = page_token
                    response = await client.get(
                        f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events",
                        params=params,
                        headers={"Authorization": f"Bearer {token}"},
                    )
                    response.raise_for_status()
                    payload = response.json()
                    for event in payload.get("items", []):
                        discovered.append(_event_to_object(calendar_id, event))
                    page_token = payload.get("nextPageToken")
                    if not page_token:
                        break
        return discovered


def _event_to_object(calendar_id: str, event: dict[str, object]) -> DiscoveredObject:
    event_id = str(event.get("id", ""))
    etag = str(event.get("etag", ""))
    summary = str(event.get("summary", "(no title)"))
    description = str(event.get("description", ""))
    start = _format_time(event.get("start"))
    end = _format_time(event.get("end"))
    location = str(event.get("location", ""))
    text = "\n".join(
        [
            f"Event: {summary}",
            f"When: {start} — {end}",
            f"Location: {location}" if location else "",
            "",
            description,
        ]
    ).strip()
    external_id = f"{calendar_id}:{event_id}"
    return DiscoveredObject(
        external_id=external_id,
        object_type="calendar_event",
        content_hash=content_hash_from_parts(calendar_id, event_id, etag),
        mime_type="text/calendar",
        content_ref=inline_content_ref(text.encode("utf-8")),
    )


def _format_time(value: object) -> str:
    if not isinstance(value, dict):
        return ""
    if value.get("dateTime"):
        return str(value["dateTime"])
    if value.get("date"):
        return str(value["date"])
    return ""
