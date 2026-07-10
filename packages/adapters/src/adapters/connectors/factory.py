from adapters.connectors.github import GitHubConnector
from adapters.connectors.google.calendar import GoogleCalendarConnector
from adapters.connectors.google.drive import GoogleDriveConnector
from adapters.connectors.google.gmail import GmailConnector
from adapters.connectors.google.oauth import GoogleOAuthService
from adapters.connectors.local_folder import LocalFolderConnector
from domain.sources import Source, SourceType
from domain.sync import DiscoveredObject


class ConnectorFactory:
    def __init__(self, *, oauth: GoogleOAuthService) -> None:
        self._local = LocalFolderConnector()
        self._github = GitHubConnector()
        self._drive = GoogleDriveConnector(oauth)
        self._gmail = GmailConnector(oauth)
        self._calendar = GoogleCalendarConnector(oauth)

    async def discover(self, source: Source) -> list[DiscoveredObject]:
        if source.type == SourceType.LOCAL_FOLDER:
            return await self._local.discover(source)
        if source.type == SourceType.GITHUB:
            return await self._github.discover(source)
        if source.type == SourceType.GOOGLE_DRIVE:
            return await self._drive.discover(source)
        if source.type == SourceType.GMAIL:
            return await self._gmail.discover(source)
        if source.type == SourceType.GOOGLE_CALENDAR:
            return await self._calendar.discover(source)
        msg = f"Unsupported source type: {source.type}"
        raise ValueError(msg)
