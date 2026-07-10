from adapters.graph.projector import Neo4jGraphProjector

from application.ports.canonical import OutboxRepository


class GraphProjectionService:
    """Process outbox events and project to Neo4j."""

    def __init__(self, outbox: OutboxRepository, projector: Neo4jGraphProjector) -> None:
        self._outbox = outbox
        self._projector = projector

    async def process_pending(self, *, batch_size: int = 50) -> int:
        await self._projector.ensure_constraints()
        events = await self._outbox.fetch_pending(limit=batch_size)
        processed = 0
        for event in events:
            try:
                await self._projector.project_event(event)
                await self._outbox.mark_processed(event.id)
                processed += 1
            except Exception as exc:  # noqa: BLE001
                await self._outbox.mark_failed(event.id, error=str(exc))
        return processed
