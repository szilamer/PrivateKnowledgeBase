from uuid import UUID

from celery import Celery


class CeleryTaskDispatcher:
    def __init__(self, broker_url: str) -> None:
        self._client = Celery(broker=broker_url)

    async def enqueue_sync_run(self, sync_run_id: UUID) -> None:
        self._client.send_task(
            "worker.tasks.ingestion.run_sync",
            args=[str(sync_run_id)],
            queue="ingestion",
        )

    async def enqueue_projection(self) -> None:
        self._client.send_task(
            "worker.tasks.graph_projection.process_pending",
            queue="graph_projection",
        )

    async def enqueue_projection_rebuild(self, owner_id: UUID) -> None:
        self._client.send_task(
            "worker.tasks.maintenance.rebuild_projection",
            args=[str(owner_id)],
            queue="maintenance",
        )
