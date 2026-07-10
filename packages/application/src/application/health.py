from domain.health import HealthStatus, ServiceHealth, SystemHealth


class HealthService:
    """Aggregates health signals from infrastructure adapters."""

    def __init__(self, version: str = "0.1.0") -> None:
        self._version = version

    def check(self, dependencies: list[ServiceHealth] | None = None) -> SystemHealth:
        services = dependencies or []
        if any(service.status == HealthStatus.UNHEALTHY for service in services):
            overall = HealthStatus.UNHEALTHY
        elif any(service.status == HealthStatus.DEGRADED for service in services):
            overall = HealthStatus.DEGRADED
        else:
            overall = HealthStatus.HEALTHY

        return SystemHealth(status=overall, services=services, version=self._version)
