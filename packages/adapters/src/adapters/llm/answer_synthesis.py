import json
import os
import re
from datetime import UTC, datetime
from typing import Protocol

import httpx
from domain.questions import AnswerClaim, Citation, QuestionAnswer


class SynthesisSettings(Protocol):
    llm_base_url: str
    llm_api_key: str
    synthesis_model: str


class HeuristicAnswerSynthesizer:
    """Offline fallback when LLM is unavailable."""

    model = "heuristic"

    async def synthesize(self, question: str, citations: list[Citation]) -> QuestionAnswer:
        now = datetime.now(UTC)
        excerpts = [citation.excerpt for citation in citations[:5]]
        joined = "\n\n".join(f"- {text[:300]}" for text in excerpts)
        answer = (
            f"Based on {len(citations)} retrieved evidence item(s):\n\n{joined}\n\n"
            f"This is a heuristic summary for: {question}"
        )
        claims = [
            AnswerClaim(
                text=excerpt[:200],
                confidence=min(citation.score, 1.0),
                citation_ids=[citation.citation_id],
            )
            for citation, excerpt in zip(citations[:3], excerpts, strict=False)
        ]
        confidence = min(max((c.score for c in citations), default=0.0), 1.0)
        return QuestionAnswer(
            question=question,
            answer=answer,
            confidence=confidence,
            insufficient_evidence=confidence < 0.3,
            citations=citations,
            claims=claims,
            model=self.model,
            created_at=now,
        )


class OpenAICompatibleAnswerSynthesizer:
    """LLM-backed answer synthesis with mandatory citation references."""

    provider = "openai_compatible"

    def __init__(self, settings: SynthesisSettings, fallback: HeuristicAnswerSynthesizer) -> None:
        self.model = settings.synthesis_model or "gpt-4o-mini"
        self._base_url = settings.llm_base_url.rstrip("/")
        self._api_key = settings.llm_api_key or os.environ.get("LLM_API_KEY", "")
        self._fallback = fallback

    async def synthesize(self, question: str, citations: list[Citation]) -> QuestionAnswer:
        try:
            return await self._synthesize_llm(question, citations)
        except Exception:  # noqa: BLE001
            return await self._fallback.synthesize(question, citations)

    async def _synthesize_llm(self, question: str, citations: list[Citation]) -> QuestionAnswer:
        context_lines = []
        for index, citation in enumerate(citations):
            context_lines.append(f"[{index}] ({citation.citation_id}) {citation.excerpt[:600]}")
        context = "\n".join(context_lines)
        prompt = (
            "Answer the question using ONLY the evidence below. "
            "Return JSON with keys: answer (string), confidence (0-1), "
            "claims (array of {text, confidence, citation_ids}), "
            "insufficient_evidence (boolean), warnings (array of strings), "
            "conflicts (array of strings). "
            "Every material claim MUST reference citation_ids from the evidence."
        )
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": prompt},
                {
                    "role": "user",
                    "content": f"Question: {question}\n\nEvidence:\n{context}",
                },
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
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

        claims = [
            AnswerClaim(
                text=str(item.get("text", "")),
                confidence=float(item.get("confidence", 0.5)),
                citation_ids=[str(cid) for cid in item.get("citation_ids", [])],
            )
            for item in parsed.get("claims", [])
            if isinstance(item, dict)
        ]
        return QuestionAnswer(
            question=question,
            answer=str(parsed.get("answer", "")),
            confidence=float(parsed.get("confidence", 0.5)),
            insufficient_evidence=bool(parsed.get("insufficient_evidence", False)),
            citations=citations,
            claims=claims,
            warnings=[str(item) for item in parsed.get("warnings", []) if item],
            conflicts=[str(item) for item in parsed.get("conflicts", []) if item],
            model=self.model,
            created_at=datetime.now(UTC),
        )


def tokenize_query(query: str) -> list[str]:
    return [token for token in re.split(r"\W+", query.lower()) if len(token) > 2]
