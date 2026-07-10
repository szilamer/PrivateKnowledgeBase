from pathlib import Path

import yaml  # type: ignore[import-untyped]
from domain.source_config import SourcesFileConfig


def load_sources_config(path: Path) -> SourcesFileConfig | None:
    if not path.is_file():
        return None
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if raw is None:
        return SourcesFileConfig()
    return SourcesFileConfig.model_validate(raw)


def save_sources_config(path: Path, config: SourcesFileConfig) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = config.model_dump(mode="json", exclude_none=True)
    path.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def redact_sources_config(config: SourcesFileConfig) -> dict[str, object]:
    return config.model_dump(mode="json")
