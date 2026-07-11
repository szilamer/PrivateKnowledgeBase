from pathlib import Path
from uuid import uuid4

from adapters.extractors.heuristic import HeuristicExtractor
from domain.extraction_validation import validate_extraction_result

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "extraction"

GOLDEN_EXPECTATIONS = {
    "sample-knowledge.md": {"min_entities": 4, "min_tasks": 2, "min_decisions": 1},
    "project-alpha.md": {"min_entities": 2, "min_tasks": 1, "min_decisions": 0},
    "meeting-notes.md": {"min_entities": 1, "min_tasks": 0, "min_decisions": 1},
    "tech-stack.txt": {"min_entities": 3, "min_tasks": 0, "min_decisions": 0},
    "minimal.md": {"min_entities": 0, "min_tasks": 0, "min_decisions": 0},
}


def _chunk_pairs(text: str) -> list[tuple[object, str]]:
    return [(uuid4(), text)]


def test_golden_extraction_fixtures() -> None:
    extractor = HeuristicExtractor()
    for filename, expected in GOLDEN_EXPECTATIONS.items():
        text = (FIXTURES_DIR / filename).read_text(encoding="utf-8")
        result = extractor.extract(text, _chunk_pairs(text))  # type: ignore[arg-type]
        passed, errors = validate_extraction_result(result)
        assert passed is True, f"{filename} validation failed: {errors}"
        assert len(result.entities) >= expected["min_entities"], filename
        assert len(result.tasks) >= expected["min_tasks"], filename
        assert len(result.decisions) >= expected["min_decisions"], filename
