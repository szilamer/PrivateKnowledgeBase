from application.health import HealthService
from domain.health import HealthStatus, ServiceHealth


def test_health_service_reports_healthy_when_all_dependencies_ok() -> None:
    service = HealthService(version="0.1.0")
    result = service.check(
        [
            ServiceHealth(name="postgres", status=HealthStatus.HEALTHY),
            ServiceHealth(name="redis", status=HealthStatus.HEALTHY),
        ]
    )
    assert result.status == HealthStatus.HEALTHY
    assert result.version == "0.1.0"


def test_health_service_reports_unhealthy_when_any_dependency_fails() -> None:
    service = HealthService()
    result = service.check(
        [
            ServiceHealth(name="postgres", status=HealthStatus.HEALTHY),
            ServiceHealth(
                name="neo4j",
                status=HealthStatus.UNHEALTHY,
                message="connection refused",
            ),
        ]
    )
    assert result.status == HealthStatus.UNHEALTHY
