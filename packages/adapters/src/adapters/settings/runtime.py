from pathlib import Path

from adapters.settings.resolver import ResolvedLlmSettings, resolve_llm_settings


def load_resolved_llm_settings(env: object) -> ResolvedLlmSettings:
    config_path = Path(getattr(env, "settings_config_path", "config/settings.yaml"))
    secrets_path = Path(getattr(env, "llm_secrets_path", "config/llm-secrets.json"))
    return resolve_llm_settings(env, config_path, secrets_path)  # type: ignore[arg-type]
