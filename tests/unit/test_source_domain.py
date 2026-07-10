import pytest
from domain.source_config import LocalFolderSourceConfig, SourcesFileConfig
from domain.sources import (
    RegisterLocalSourceCommand,
    SourceType,
    source_id_for_config,
)


def test_register_local_source_command_defaults() -> None:
    cmd = RegisterLocalSourceCommand(name="Docs", path="/tmp/docs")
    assert cmd.file_extensions == [".md", ".txt", ".pdf"]
    assert cmd.enabled is True


def test_register_local_source_command_paths() -> None:
    cmd = RegisterLocalSourceCommand(name="Docs", paths=["~/Projects", "~/Docs"])
    assert cmd.paths == ["~/Projects", "~/Docs"]


def test_source_type_values() -> None:
    assert SourceType.LOCAL_FOLDER.value == "local_folder"
    assert SourceType.GITHUB.value == "github"
    assert SourceType.GOOGLE_DRIVE.value == "google_drive"
    assert SourceType.GMAIL.value == "gmail"
    assert SourceType.GOOGLE_CALENDAR.value == "google_calendar"


def test_source_id_for_config_is_stable() -> None:
    first = source_id_for_config("projects-local")
    second = source_id_for_config("projects-local")
    assert first == second


def test_sources_file_config_validation() -> None:
    config = SourcesFileConfig.model_validate(
        {
            "version": "1",
            "sources": [
                {
                    "id": "projects-local",
                    "type": "local_folder",
                    "name": "Projektek",
                    "paths": ["~/Projects"],
                }
            ],
        }
    )
    assert len(config.sources) == 1
    entry = config.sources[0]
    assert isinstance(entry, LocalFolderSourceConfig)
    assert entry.paths == ["~/Projects"]


def test_sources_file_config_rejects_duplicate_ids() -> None:
    with pytest.raises(ValueError):
        SourcesFileConfig.model_validate(
            {
                "sources": [
                    {"id": "a", "type": "local_folder", "name": "A", "paths": ["/a"]},
                    {"id": "a", "type": "gmail", "name": "B", "query": "is:important"},
                ]
            }
        )
