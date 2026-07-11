from adapters.connectors.google.factory import build_google_oauth
from adapters.content.loader import LocalAndGitHubContentLoader
from sqlalchemy.ext.asyncio import AsyncSession

from worker.config import Settings


def build_content_loader(session: AsyncSession, settings: Settings) -> LocalAndGitHubContentLoader:
    oauth = build_google_oauth(
        session=session,
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        redirect_uri=settings.google_redirect_uri,
        session_secret=settings.session_secret,
        enabled=settings.pkb_google_connectors_enabled,
    )
    return LocalAndGitHubContentLoader(oauth)
