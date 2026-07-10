from pathlib import Path

import pytest
from application.sources.browse_service import HostPathMapper, LocalFolderBrowseService
from domain.errors import DomainError


def test_host_path_mapper_roundtrip(tmp_path: Path) -> None:
    host_root = tmp_path / "host"
    projects = host_root / "Projects"
    projects.mkdir(parents=True)
    mapper = HostPathMapper(str(host_root))
    assert mapper.to_filesystem("~/Projects") == projects.resolve()
    assert mapper.to_display(projects) == "~/Projects"


def test_browse_lists_child_directories(tmp_path: Path) -> None:
    host_root = tmp_path / "host"
    docs = host_root / "Documents"
    nested = docs / "Notes"
    nested.mkdir(parents=True)
    service = LocalFolderBrowseService(host_root=str(host_root))
    result = service.browse("~")
    assert result.readable is True
    assert result.error is None
    names = {entry.name for entry in result.entries}
    assert "Documents" in names

    child = service.browse("~/Documents")
    assert any(entry.name == "Notes" for entry in child.entries)


def test_validate_selectable_rejects_missing(tmp_path: Path) -> None:
    host_root = tmp_path / "host"
    host_root.mkdir()
    service = LocalFolderBrowseService(host_root=str(host_root))
    with pytest.raises(DomainError):
        service.validate_selectable("~/missing")
