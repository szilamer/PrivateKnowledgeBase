from pathlib import Path

from adapters.settings.config_loader import (
    load_app_settings,
    redact_app_settings,
    save_app_settings,
)
from adapters.settings.resolver import ResolvedLlmSettings, resolve_llm_settings, resolved_to_public
from domain.app_settings import AppSettingsFile
from domain.errors import DomainError


class AppSettingsService:
    """Declarative app settings (LLM, embeddings) in config/settings.yaml."""

    def __init__(self, config_path: Path, env: object) -> None:
        self._config_path = config_path
        self._env = env

    def get_config(self) -> AppSettingsFile:
        config = load_app_settings(self._config_path)
        if config is None:
            return AppSettingsFile()
        return config

    def get_config_redacted(self) -> dict[str, object]:
        redacted = redact_app_settings(self.get_config())
        resolved = self.get_resolved()
        redacted["effective"] = {"llm": resolved_to_public(resolved)}
        return redacted

    def get_resolved(self) -> ResolvedLlmSettings:
        return resolve_llm_settings(self._env, self._config_path)  # type: ignore[arg-type]

    def put_config(self, payload: dict[str, object]) -> AppSettingsFile:
        try:
            config = AppSettingsFile.model_validate(payload)
        except ValueError as exc:
            raise DomainError(f"Invalid app settings: {exc}") from exc
        save_app_settings(self._config_path, config)
        return config

    @property
    def config_path(self) -> Path:
        return self._config_path
