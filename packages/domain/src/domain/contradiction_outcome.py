from dataclasses import dataclass

from domain.canonical import ContradictionFinding

CONTRADICTION_PIPELINE_VERSION = "v1"


@dataclass(frozen=True)
class ContradictionDetectionOutcome:
    findings: list[ContradictionFinding]
    candidate_count: int
    pipeline_version: str = CONTRADICTION_PIPELINE_VERSION
