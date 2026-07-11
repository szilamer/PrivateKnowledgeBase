from pathlib import Path

from adapters.settings.config_loader import (
    load_app_settings,
    redact_app_settings,
    save_app_settings,
)
from adapters.settings.resolver import ResolvedLlmSettings, resolve_llm_settings, resolved_to_public
from adapters.settings.secrets_store import clear_llm_api_key, save_llm_api_key
from domain.app_settings import AppSettingsFile
from domain.errors import DomainError


class AppSettingsService:
    """Declarative app settings (LLM, embeddings) in config/settings.yaml."""

    def __init__(self, config_path: Path, env: object, secrets_path: Path) -> None:
        self._config_path = config_path
        self._env = env
        self._secrets_path = secrets_path

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
        return resolve_llm_settings(self._env, self._config_path, self._secrets_path)  # type: ignore[arg-type]

    def set_api_key(self, api_key: str) -> None:
        trimmed = api_key.strip()
        if not trimmed:
            raise DomainError("Az API kulcs nem lehet üres.")
        try:
            save_llm_api_key(self._secrets_path, trimmed)
        except OSError as exc:
            raise DomainError(f"Nem sikerült menteni az API kulcsot: {exc}") from exc

    def clear_api_key(self) -> None:
        try:
            clear_llm_api_key(self._secrets_path)
        except OSError as exc:
            raise DomainError(f"Nem sikerült törölni az API kulcsot: {exc}") from exc

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

    @property
    def secrets_path(self) -> Path:
        return self._secrets_path
