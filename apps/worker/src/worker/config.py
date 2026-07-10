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
