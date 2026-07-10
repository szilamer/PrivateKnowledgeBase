from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    database_url: str = "postgresql+asyncpg://pkb:change-me-in-production@localhost:5432/pkb"
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "change-me-in-production"
    session_secret: str = "change-me-to-a-random-32-byte-string"
    sources_config_path: str = "config/sources.yaml"
    settings_config_path: str = "config/settings.yaml"
    host_path_manifest_path: str = "config/host-path-manifest.json"
    pkb_host_root: str = "/host"
    pkb_source_dirs: str = ""
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/v1/connectors/google/callback"
    pkb_google_connectors_enabled: bool = False
    sources_bootstrap_on_startup: bool = True
    llm_base_url: str = "http://localhost:11434/v1"
    llm_api_key: str = ""
    embedding_model: str = "text-embedding-3-small"
    embedding_dimension: int = 1536
    extraction_model: str = "gpt-4o-mini"
    synthesis_model: str = "gpt-4o-mini"
