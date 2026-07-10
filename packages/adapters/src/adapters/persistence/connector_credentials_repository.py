import json
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class ConnectorCredential:
    id: UUID
    owner_id: UUID
    provider: str
    account_alias: str
    email: str | None
    refresh_token_encrypted: str
    scopes: list[str]
    sync_state: dict[str, object]


class PostgresConnectorCredentialsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(
        self,
        *,
        owner_id: UUID,
        provider: str,
        account_alias: str,
        email: str | None,
        refresh_token_encrypted: str,
        scopes: list[str],
    ) -> ConnectorCredential:
        credential_id = uuid4()
        now = datetime.now(UTC)
        await self._session.execute(
            text(
                """
                INSERT INTO connector_credentials (
                    id, owner_id, provider, account_alias, email,
                    refresh_token_encrypted, scopes, updated_at
                ) VALUES (
                    :id, :owner_id, :provider, :account_alias, :email,
                    :refresh_token_encrypted, :scopes, :updated_at
                )
                ON CONFLICT (owner_id, provider, account_alias) DO UPDATE SET
                    email = EXCLUDED.email,
                    refresh_token_encrypted = EXCLUDED.refresh_token_encrypted,
                    scopes = EXCLUDED.scopes,
                    updated_at = EXCLUDED.updated_at
                """
            ),
            {
                "id": credential_id,
                "owner_id": owner_id,
                "provider": provider,
                "account_alias": account_alias,
                "email": email,
                "refresh_token_encrypted": refresh_token_encrypted,
                "scopes": scopes,
                "updated_at": now,
            },
        )
        result = await self.get(owner_id, provider, account_alias)
        assert result is not None
        return result

    async def get(
        self, owner_id: UUID, provider: str, account_alias: str
    ) -> ConnectorCredential | None:
        result = await self._session.execute(
            text(
                """
                SELECT * FROM connector_credentials
                WHERE owner_id = :owner_id AND provider = :provider
                  AND account_alias = :account_alias
                """
            ),
            {
                "owner_id": owner_id,
                "provider": provider,
                "account_alias": account_alias,
            },
        )
        row = result.first()
        if row is None:
            return None
        mapping = dict(row._mapping)
        return ConnectorCredential(
            id=mapping["id"],
            owner_id=mapping["owner_id"],
            provider=mapping["provider"],
            account_alias=mapping["account_alias"],
            email=mapping["email"],
            refresh_token_encrypted=mapping["refresh_token_encrypted"],
            scopes=list(mapping["scopes"] or []),
            sync_state=mapping.get("sync_state") or {},
        )

    async def list_by_owner(self, owner_id: UUID) -> list[ConnectorCredential]:
        result = await self._session.execute(
            text("SELECT * FROM connector_credentials WHERE owner_id = :owner_id"),
            {"owner_id": owner_id},
        )
        rows = result.fetchall()
        credentials: list[ConnectorCredential] = []
        for row in rows:
            mapping = dict(row._mapping)
            credentials.append(
                ConnectorCredential(
                    id=mapping["id"],
                    owner_id=mapping["owner_id"],
                    provider=mapping["provider"],
                    account_alias=mapping["account_alias"],
                    email=mapping["email"],
                    refresh_token_encrypted=mapping["refresh_token_encrypted"],
                    scopes=list(mapping["scopes"] or []),
                    sync_state=mapping.get("sync_state") or {},
                )
            )
        return credentials

    async def delete(self, owner_id: UUID, provider: str, account_alias: str) -> bool:
        result = await self._session.execute(
            text(
                """
                DELETE FROM connector_credentials
                WHERE owner_id = :owner_id AND provider = :provider
                  AND account_alias = :account_alias
                """
            ),
            {
                "owner_id": owner_id,
                "provider": provider,
                "account_alias": account_alias,
            },
        )
        return result.rowcount > 0  # type: ignore[attr-defined,no-any-return]

    async def update_sync_state(
        self,
        owner_id: UUID,
        provider: str,
        account_alias: str,
        sync_state: dict[str, object],
    ) -> None:
        await self._session.execute(
            text(
                """
                UPDATE connector_credentials
                SET sync_state = CAST(:sync_state AS jsonb), updated_at = NOW()
                WHERE owner_id = :owner_id AND provider = :provider
                  AND account_alias = :account_alias
                """
            ),
            {
                "owner_id": owner_id,
                "provider": provider,
                "account_alias": account_alias,
                "sync_state": json.dumps(sync_state),
            },
        )
