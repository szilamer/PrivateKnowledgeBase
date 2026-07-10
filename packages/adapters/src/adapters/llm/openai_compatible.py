import json
import os
from typing import Protocol

import httpx
from domain.extraction import ExtractionResult


class LLMSettings(Protocol):
    llm_base_url: str
    llm_api_key: str
    extraction_model: str


class OpenAICompatibleLLMProvider:
    """ADR-007 — OpenAI-compatible chat completions for structured extraction."""

    provider = "openai_compatible"

    def __init__(self, settings: LLMSettings) -> None:
        self.model = settings.extraction_model or "gpt-4o-mini"
        self._base_url = settings.llm_base_url.rstrip("/")
        self._api_key = settings.llm_api_key or os.environ.get("LLM_API_KEY", "")

    async def extract_knowledge(self, text: str, schema_version: str) -> ExtractionResult:
        prompt = (
            "Extract structured knowledge from the document below. "
            "Return JSON matching schema version "
            f"{schema_version} with keys: entities, claims, relationships, "
            "tasks, decisions, events, warnings. "
            "Each entity needs local_id, name, entity_type "
            "(project|person|organization|document|repository|technology|concept|"
            "system_component|external_system), confidence 0-1. "
            "Include evidence anchors when possible."
        )
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": text[:12000]},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.1,
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self._base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            body = response.json()
            content = body["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            parsed.setdefault("schema_version", schema_version)
            return ExtractionResult.model_validate(parsed)

    async def is_available(self) -> bool:
        if not self._base_url:
            return False
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self._base_url.replace('/v1', '')}/health")
                return response.status_code < 500
        except Exception:  # noqa: BLE001
            return bool(self._api_key)
