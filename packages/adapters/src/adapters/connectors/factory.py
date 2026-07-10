from adapters.connectors.github import GitHubConnector
from adapters.connectors.local_folder import LocalFolderConnector
from domain.sources import Source, SourceType
from domain.sync import DiscoveredObject


class ConnectorFactory:
    def __init__(self) -> None:
        self._local = LocalFolderConnector()
        self._github = GitHubConnector()

    async def discover(self, source: Source) -> list[DiscoveredObject]:
        if source.type == SourceType.LOCAL_FOLDER:
            return await self._local.discover(source)
        if source.type == SourceType.GITHUB:
            return await self._github.discover(source)
        msg = f"Unsupported source type: {source.type}"
        raise ValueError(msg)
