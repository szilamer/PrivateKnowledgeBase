from adapters.extractors.heuristic import HeuristicExtractor
from domain.entities import EntityType


def test_heuristic_extractor_finds_technologies_and_tasks() -> None:
    text = """
# Atlas Project

We decided to use PostgreSQL and FastAPI.

TODO: implement approval queue
"""
    extractor = HeuristicExtractor()
    result = extractor.extract(text, [])
    types = {entity.entity_type for entity in result.entities}
    assert EntityType.TECHNOLOGY in types
    assert EntityType.PROJECT in types or EntityType.CONCEPT in types
    assert len(result.tasks) >= 1
    assert len(result.decisions) >= 1
