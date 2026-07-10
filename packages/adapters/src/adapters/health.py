import asyncio
from typing import Protocol

from domain.health import HealthStatus, ServiceHealth
from neo4j import AsyncGraphDatabase
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine


class HealthCheckerConfig(Protocol):
    database_url: str
    redis_url: str
    neo4j_uri: str
    neo4j_user: str
    neo4j_password: str


class HealthChecker:
    def __init__(self, config: HealthCheckerConfig) -> None:
        self._config = config
        self._engine: AsyncEngine = create_async_engine(config.database_url, pool_pre_ping=True)

    async def check_postgres(self) -> ServiceHealth:
        try:
            async with self._engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
            return ServiceHealth(name="postgres", status=HealthStatus.HEALTHY)
        except Exception as exc:  # noqa: BLE001 — health probe must capture all failures
            return ServiceHealth(name="postgres", status=HealthStatus.UNHEALTHY, message=str(exc))

    async def check_redis(self) -> ServiceHealth:
        client = Redis.from_url(self._config.redis_url)
        try:
            await client.ping()
            return ServiceHealth(name="redis", status=HealthStatus.HEALTHY)
        except Exception as exc:  # noqa: BLE001
            return ServiceHealth(name="redis", status=HealthStatus.UNHEALTHY, message=str(exc))
        finally:
            await client.aclose()

    async def check_neo4j(self) -> ServiceHealth:
        driver = AsyncGraphDatabase.driver(
            self._config.neo4j_uri,
            auth=(self._config.neo4j_user, self._config.neo4j_password),
        )
        try:
            await driver.verify_connectivity()
            return ServiceHealth(name="neo4j", status=HealthStatus.HEALTHY)
        except Exception as exc:  # noqa: BLE001
            return ServiceHealth(name="neo4j", status=HealthStatus.UNHEALTHY, message=str(exc))
        finally:
            await driver.close()

    async def check_all(self) -> list[ServiceHealth]:
        return list(
            await asyncio.gather(
                self.check_postgres(),
                self.check_redis(),
                self.check_neo4j(),
            )
        )

    async def dispose(self) -> None:
        await self._engine.dispose()
