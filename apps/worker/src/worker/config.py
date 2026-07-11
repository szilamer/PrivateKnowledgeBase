from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    log_level: str = "INFO"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"
    database_url: str = "postgresql+asyncpg://pkb:change-me-in-production@localhost:5432/pkb"
    redis_url: str = "redis://localhost:6379/0"
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "change-me-in-production"
    llm_base_url: str = "http://localhost:11434/v1"
    llm_api_key: str = ""
    embedding_model: str = "text-embedding-3-small"
    embedding_dimension: int = 1536
    extraction_model: str = "gpt-4o-mini"
    synthesis_model: str = "gpt-4o-mini"
    settings_config_path: str = "config/settings.yaml"
    llm_secrets_path: str = "config/llm-secrets.json"
    session_secret: str = "change-me-to-a-random-32-byte-string"
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/v1/connectors/google/callback"
    pkb_google_connectors_enabled: bool = False
