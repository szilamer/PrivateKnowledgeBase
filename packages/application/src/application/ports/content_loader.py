from typing import Protocol
from uuid import UUID


class ContentLoader(Protocol):
    async def load(self, version_id: UUID, record: dict[str, object]) -> bytes: ...
