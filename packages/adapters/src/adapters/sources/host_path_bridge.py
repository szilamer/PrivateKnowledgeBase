import json
from pathlib import Path


class HostPathBridge:
    """FR-SRC-011 — map host paths to container-visible paths via manifest or /host mount."""

    def __init__(self, manifest_path: Path, host_root: str = "/host") -> None:
        self._mappings: dict[str, str] = {}
        if manifest_path.is_file():
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
            raw = data.get("mappings", {})
            if isinstance(raw, dict):
                self._mappings = {str(k): str(v) for k, v in raw.items()}
        self._host_root = Path(host_root).resolve() if host_root else None

    def resolve(self, path: str) -> str:
        expanded = str(Path(path).expanduser())
        if path in self._mappings:
            return self._mappings[path]
        if expanded in self._mappings:
            return self._mappings[expanded]
        if self._host_root is not None and (path == "~" or path.startswith("~/")):
            suffix = path[2:] if path.startswith("~/") else ""
            candidate = self._host_root if not suffix else self._host_root / suffix
            return str(candidate.resolve())
        return expanded

    def resolve_many(self, paths: list[str]) -> list[str]:
        return [self.resolve(item) for item in paths]
