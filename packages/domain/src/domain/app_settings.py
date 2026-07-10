from typing import Literal

from pydantic import BaseModel, Field


class EmbeddingSettingsConfig(BaseModel):
    provider: Literal["auto", "hash", "api"] = "auto"
    model: str = "text-embedding-3-small"
    dimension: int = 1536


class LlmSettingsConfig(BaseModel):
    enabled: bool = True
    base_url: str = "http://localhost:11434/v1"
    api_key_env: str = "LLM_API_KEY"
    extraction_model: str = "gpt-4o-mini"
    synthesis_model: str = "gpt-4o-mini"
    embedding: EmbeddingSettingsConfig = Field(default_factory=EmbeddingSettingsConfig)


class AppSettingsFile(BaseModel):
    version: str = "1"
    llm: LlmSettingsConfig = Field(default_factory=LlmSettingsConfig)
