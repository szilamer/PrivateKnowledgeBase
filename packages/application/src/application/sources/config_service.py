from pathlib import Path

from adapters.sources.config_loader import (
    load_sources_config,
    redact_sources_config,
    save_sources_config,
)
from domain.errors import DomainError
from domain.source_config import SourcesFileConfig


class SourceConfigService:
    """FR-SRC-010 — read and write declarative sources configuration."""

    def __init__(self, config_path: Path) -> None:
        self._config_path = config_path

    def get_config(self) -> SourcesFileConfig:
        config = load_sources_config(self._config_path)
        if config is None:
            return SourcesFileConfig()
        return config

    def get_config_redacted(self) -> dict[str, object]:
        return redact_sources_config(self.get_config())

    def put_config(self, payload: dict[str, object]) -> SourcesFileConfig:
        try:
            config = SourcesFileConfig.model_validate(payload)
        except ValueError as exc:
            raise DomainError(f"Invalid sources configuration: {exc}") from exc
        try:
            save_sources_config(self._config_path, config)
        except OSError as exc:
            raise DomainError(
                f"Cannot write sources configuration to {self._config_path}: {exc}"
            ) from exc
        return config

    @property
    def config_path(self) -> Path:
        return self._config_path
