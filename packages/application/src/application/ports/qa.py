from typing import Protocol

from domain.questions import Citation, QuestionAnswer


class AnswerSynthesizer(Protocol):
    model: str

    async def synthesize(self, question: str, citations: list[Citation]) -> QuestionAnswer: ...
