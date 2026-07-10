import os
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from adapters.settings.config_loader import load_app_settings
from domain.app_settings import AppSettingsFile


class EnvLlmDefaults(Protocol):
    llm_base_url: str
    llm_api_key: str
    embedding_model: str
    embedding_dimension: int
    extraction_model: str
    synthesis_model: str


@dataclass
class ResolvedLlmSettings:
    llm_base_url: str
    llm_api_key: str
    extraction_model: str
    synthesis_model: str
    embedding_model: str
    embedding_dimension: int
    use_hash_embeddings: bool
    llm_enabled: bool
    api_key_env: str
    api_key_configured: bool


def resolve_llm_settings(
    env: EnvLlmDefaults,
    config_path: Path,
) -> ResolvedLlmSettings:
    file_config = load_app_settings(config_path) or AppSettingsFile()
    llm = file_config.llm
    api_key = os.environ.get(llm.api_key_env, "") or env.llm_api_key
    use_hash = _resolve_embedding_mode(llm.embedding.provider, api_key)
    return ResolvedLlmSettings(
        llm_base_url=llm.base_url or env.llm_base_url,
        llm_api_key=api_key,
        extraction_model=llm.extraction_model or env.extraction_model,
        synthesis_model=llm.synthesis_model or env.synthesis_model,
        embedding_model=llm.embedding.model or env.embedding_model,
        embedding_dimension=llm.embedding.dimension or env.embedding_dimension,
        use_hash_embeddings=use_hash,
        llm_enabled=llm.enabled,
        api_key_env=llm.api_key_env,
        api_key_configured=bool(api_key),
    )


def _resolve_embedding_mode(provider: str, api_key: str) -> bool:
    if provider == "hash":
        return True
    if provider == "api":
        return False
    return not api_key


def resolved_to_public(resolved: ResolvedLlmSettings) -> dict[str, object]:
    return {
        "enabled": resolved.llm_enabled,
        "base_url": resolved.llm_base_url,
        "api_key_env": resolved.api_key_env,
        "api_key_configured": resolved.api_key_configured,
        "extraction_model": resolved.extraction_model,
        "synthesis_model": resolved.synthesis_model,
        "embedding": {
            "provider": "hash" if resolved.use_hash_embeddings else "api",
            "model": resolved.embedding_model,
            "dimension": resolved.embedding_dimension,
        },
    }
