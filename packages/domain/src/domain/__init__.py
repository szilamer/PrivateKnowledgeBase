"""Domain layer — framework-independent business types and rules."""

from domain.errors import DomainError
from domain.health import HealthStatus, ServiceHealth

__all__ = ["DomainError", "HealthStatus", "ServiceHealth"]
