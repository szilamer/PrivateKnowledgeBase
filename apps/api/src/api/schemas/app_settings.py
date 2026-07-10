from pydantic import BaseModel, Field


class AppSettingsResponse(BaseModel):
    config: dict[str, object]
    config_path: str


class AppSettingsPutRequest(BaseModel):
    config: dict[str, object] = Field(default_factory=dict)


class LlmHealthResponse(BaseModel):
    status: str
    llm_enabled: bool
    api_key_configured: bool
    base_url: str
    extraction_model: str
    synthesis_model: str
    embedding_provider: str
    message: str | None = None
