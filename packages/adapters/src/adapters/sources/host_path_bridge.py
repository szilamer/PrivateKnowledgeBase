import json
from pathlib import Path


class HostPathBridge:
    """FR-SRC-011 — map host paths to container-visible paths via manifest."""

    def __init__(self, manifest_path: Path) -> None:
        self._mappings: dict[str, str] = {}
        if manifest_path.is_file():
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
            raw = data.get("mappings", {})
            if isinstance(raw, dict):
                self._mappings = {str(k): str(v) for k, v in raw.items()}

    def resolve(self, path: str) -> str:
        expanded = str(Path(path).expanduser())
        if path in self._mappings:
            return self._mappings[path]
        if expanded in self._mappings:
            return self._mappings[expanded]
        return expanded

    def resolve_many(self, paths: list[str]) -> list[str]:
        return [self.resolve(item) for item in paths]
