import asyncio
from collections.abc import AsyncIterator, Callable, Coroutine
from contextlib import asynccontextmanager
from typing import Any

from adapters.persistence.session import create_engine, create_session_factory, session_scope
from sqlalchemy.ext.asyncio import AsyncSession

from worker.config import Settings

settings = Settings()


@asynccontextmanager
async def task_session() -> AsyncIterator[AsyncSession]:
    """Fresh engine per Celery task — avoids asyncio loop / pool cross-talk."""
    engine = create_engine(settings.database_url)
    factory = create_session_factory(engine)
    try:
        async with session_scope(factory) as session:
            yield session
    finally:
        await engine.dispose()


def run_task[T](coro: Callable[[], Coroutine[Any, Any, T]]) -> T:
    return asyncio.run(coro())
