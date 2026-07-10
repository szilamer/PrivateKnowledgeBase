from adapters.connectors.factory import ConnectorFactory
from adapters.connectors.google.oauth import GoogleOAuthService
from adapters.persistence.connector_credentials_repository import (
    PostgresConnectorCredentialsRepository,
)
from adapters.sources.token_encryption import TokenEncryption


def build_google_oauth(
    *,
    session: object,
    client_id: str,
    client_secret: str,
    redirect_uri: str,
    session_secret: str,
    enabled: bool,
) -> GoogleOAuthService:
    encryption = TokenEncryption(session_secret)
    credentials_repo = PostgresConnectorCredentialsRepository(session)  # type: ignore[arg-type]
    return GoogleOAuthService(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        encryption=encryption,
        credentials_repo=credentials_repo,
        enabled=enabled,
    )


def build_connector_factory(oauth: GoogleOAuthService) -> ConnectorFactory:
    return ConnectorFactory(oauth=oauth)
