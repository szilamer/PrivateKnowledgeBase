from pydantic import BaseModel, Field


class SourcesConfigResponse(BaseModel):
    config: dict[str, object]
    config_path: str


class SourcesConfigPutRequest(BaseModel):
    config: dict[str, object] = Field(default_factory=dict)


class SourcesHealthResponse(BaseModel):
    status: str
    config_path: str
    config_loaded: bool
    source_count: int
    errors: list[str] = Field(default_factory=list)
    google_connectors_enabled: bool
