from pathlib import Path

from adapters.settings.resolver import ResolvedLlmSettings, resolve_llm_settings


def load_resolved_llm_settings(env: object) -> ResolvedLlmSettings:
    config_path = Path(getattr(env, "settings_config_path", "config/settings.yaml"))
    return resolve_llm_settings(env, config_path)  # type: ignore[arg-type]
