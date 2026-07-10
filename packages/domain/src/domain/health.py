from enum import StrEnum

from pydantic import BaseModel, Field


class HealthStatus(StrEnum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ServiceHealth(BaseModel):
    name: str
    status: HealthStatus
    message: str | None = None


class SystemHealth(BaseModel):
    status: HealthStatus
    services: list[ServiceHealth] = Field(default_factory=list)
    version: str = "0.1.0"
