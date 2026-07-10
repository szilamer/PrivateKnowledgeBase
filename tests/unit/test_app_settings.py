from pathlib import Path

from adapters.settings.config_loader import save_app_settings
from adapters.settings.resolver import resolve_llm_settings
from domain.app_settings import AppSettingsFile


def test_resolve_llm_settings_from_file(tmp_path: Path) -> None:
    config_path = tmp_path / "settings.yaml"
    save_app_settings(
        config_path,
        AppSettingsFile.model_validate(
            {
                "llm": {
                    "base_url": "http://ollama:11434/v1",
                    "extraction_model": "llama3",
                    "embedding": {"provider": "hash", "dimension": 768},
                }
            }
        ),
    )

    class Env:
        llm_base_url = "http://localhost:8000/v1"
        llm_api_key = ""
        embedding_model = "text-embedding-3-small"
        embedding_dimension = 1536
        extraction_model = "gpt-4o-mini"
        synthesis_model = "gpt-4o-mini"

    resolved = resolve_llm_settings(Env(), config_path)
    assert resolved.llm_base_url == "http://ollama:11434/v1"
    assert resolved.extraction_model == "llama3"
    assert resolved.use_hash_embeddings is True
    assert resolved.embedding_dimension == 768


def test_app_settings_file_defaults() -> None:
    config = AppSettingsFile()
    assert config.llm.enabled is True
    assert config.llm.embedding.provider == "auto"
