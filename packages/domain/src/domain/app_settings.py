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


class ExtractionAgentSettings(BaseModel):
    use_langgraph: bool = True


class PlannerAgentSettings(BaseModel):
    version: Literal["deterministic", "graph_v2"] = "graph_v2"


class SynthesisAgentSettings(BaseModel):
    version: Literal["deterministic", "graph_v2"] = "graph_v2"


class TriageAgentSettings(BaseModel):
    enabled: bool = True


class AgentsSettingsConfig(BaseModel):
    extraction: ExtractionAgentSettings = Field(default_factory=ExtractionAgentSettings)
    triage: TriageAgentSettings = Field(default_factory=TriageAgentSettings)
    planner: PlannerAgentSettings = Field(default_factory=PlannerAgentSettings)
    synthesis: SynthesisAgentSettings = Field(default_factory=SynthesisAgentSettings)


class AppSettingsFile(BaseModel):
    version: str = "1"
    llm: LlmSettingsConfig = Field(default_factory=LlmSettingsConfig)
    agents: AgentsSettingsConfig = Field(default_factory=AgentsSettingsConfig)
