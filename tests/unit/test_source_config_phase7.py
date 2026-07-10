from pathlib import Path

from adapters.sources.config_loader import load_sources_config, save_sources_config
from adapters.sources.host_path_bridge import HostPathBridge
from domain.source_config import SourcesFileConfig


def test_host_path_bridge_resolves_manifest(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        '{"mappings": {"/Users/me/Projects": "/sources/host-0", "~/Projects": "/sources/host-0"}}',
        encoding="utf-8",
    )
    bridge = HostPathBridge(manifest, host_root="/host")
    assert bridge.resolve("~/Projects") == "/sources/host-0"
    assert bridge.resolve("/Users/me/Projects") == "/sources/host-0"
    assert bridge.resolve_many(["~/Projects"]) == ["/sources/host-0"]


def test_host_path_bridge_falls_back_to_host_root(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text('{"mappings": {}}', encoding="utf-8")
    host_root = tmp_path / "host"
    (host_root / "Projects").mkdir(parents=True)
    bridge = HostPathBridge(manifest, host_root=str(host_root))
    assert bridge.resolve("~/Projects") == str((host_root / "Projects").resolve())


def test_sources_config_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "sources.yaml"
    original = SourcesFileConfig.model_validate(
        {
            "version": "1",
            "sources": [
                {
                    "id": "docs",
                    "type": "local_folder",
                    "name": "Docs",
                    "paths": ["~/Documents"],
                }
            ],
        }
    )
    save_sources_config(path, original)
    loaded = load_sources_config(path)
    assert loaded is not None
    assert loaded.model_dump() == original.model_dump()
