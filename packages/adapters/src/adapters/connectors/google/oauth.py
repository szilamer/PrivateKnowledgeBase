from __future__ import annotations

import base64
import hashlib
from urllib.parse import urlencode

import httpx
from adapters.persistence.connector_credentials_repository import (
    ConnectorCredential,
    PostgresConnectorCredentialsRepository,
)
from adapters.sources.token_encryption import TokenEncryption
from domain.identity import DEFAULT_OWNER_ID

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar.readonly",
    "openid",
    "email",
]


class GoogleOAuthService:
    """ADR-013 — Google OAuth authorization code flow."""

    def __init__(
        self,
        *,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        encryption: TokenEncryption,
        credentials_repo: PostgresConnectorCredentialsRepository,
        enabled: bool = True,
    ) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._redirect_uri = redirect_uri
        self._encryption = encryption
        self._credentials = credentials_repo
        self._enabled = enabled

    @property
    def enabled(self) -> bool:
        return self._enabled and bool(self._client_id and self._client_secret)

    def build_auth_url(self, *, state: str) -> str:
        if not self.enabled:
            msg = "Google connectors are not configured"
            raise ValueError(msg)
        params = {
            "client_id": self._client_id,
            "redirect_uri": self._redirect_uri,
            "response_type": "code",
            "scope": " ".join(GOOGLE_SCOPES),
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
        }
        return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"

    async def handle_callback(
        self, *, code: str, account_alias: str = "primary"
    ) -> ConnectorCredential:
        if not self.enabled:
            msg = "Google connectors are not configured"
            raise ValueError(msg)
        async with httpx.AsyncClient(timeout=30.0) as client:
            token_response = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "code": code,
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                    "redirect_uri": self._redirect_uri,
                    "grant_type": "authorization_code",
                },
            )
            token_response.raise_for_status()
            tokens = token_response.json()

            refresh_token = tokens.get("refresh_token")
            if not refresh_token:
                msg = "Google did not return a refresh token; reconnect with consent"
                raise ValueError(msg)

            access_token = tokens["access_token"]
            userinfo = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            userinfo.raise_for_status()
            profile = userinfo.json()

        encrypted = self._encryption.encrypt(refresh_token)
        return await self._credentials.upsert(
            owner_id=DEFAULT_OWNER_ID,
            provider="google",
            account_alias=account_alias,
            email=profile.get("email"),
            refresh_token_encrypted=encrypted,
            scopes=GOOGLE_SCOPES,
        )

    async def list_accounts(self) -> list[dict[str, object]]:
        credentials = await self._credentials.list_by_owner(DEFAULT_OWNER_ID)
        return [
            {
                "id": str(item.id),
                "provider": item.provider,
                "account_alias": item.account_alias,
                "email": item.email,
                "scopes": item.scopes,
            }
            for item in credentials
            if item.provider == "google"
        ]

    async def revoke_account(self, account_alias: str) -> bool:
        return await self._credentials.delete(DEFAULT_OWNER_ID, "google", account_alias)

    async def get_access_token(self, account: str) -> str:
        if not self.enabled:
            msg = "Google connectors are not configured"
            raise ValueError(msg)
        provider, alias = _parse_account_ref(account)
        credential = await self._credentials.get(DEFAULT_OWNER_ID, provider, alias)
        if credential is None:
            msg = f"Google account not connected: {account}"
            raise ValueError(msg)
        refresh_token = self._encryption.decrypt(credential.refresh_token_encrypted)
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token",
                },
            )
            response.raise_for_status()
            payload = response.json()
            return str(payload["access_token"])


def _parse_account_ref(account: str) -> tuple[str, str]:
    if ":" in account:
        provider, alias = account.split(":", 1)
        return provider, alias
    return "google", account


def content_hash_from_parts(*parts: str) -> str:
    joined = "|".join(parts)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def inline_content_ref(content: bytes) -> str:
    return f"inline:{base64.b64encode(content).decode('ascii')}"
