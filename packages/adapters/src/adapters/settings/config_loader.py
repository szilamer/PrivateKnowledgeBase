from pathlib import Path

import yaml  # type: ignore[import-untyped]
from domain.app_settings import AppSettingsFile


def load_app_settings(path: Path) -> AppSettingsFile | None:
    if not path.is_file():
        return None
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if raw is None:
        return AppSettingsFile()
    return AppSettingsFile.model_validate(raw)


def save_app_settings(path: Path, config: AppSettingsFile) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = config.model_dump(mode="json", exclude_none=True)
    path.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def redact_app_settings(config: AppSettingsFile) -> dict[str, object]:
    payload = config.model_dump(mode="json")
    llm = payload.get("llm")
    if isinstance(llm, dict):
        llm.pop("api_key", None)
    return payload
