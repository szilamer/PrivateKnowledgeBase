import pytest
from domain.errors import DomainError
from domain.sources import RegisterLocalSourceCommand, SourceType


def test_register_local_source_command_defaults() -> None:
    cmd = RegisterLocalSourceCommand(name="Docs", path="/tmp/docs")
    assert cmd.file_extensions == [".md", ".txt", ".pdf"]
    assert cmd.enabled is True


def test_source_type_values() -> None:
    assert SourceType.LOCAL_FOLDER.value == "local_folder"
    assert SourceType.GITHUB.value == "github"


def test_domain_error_is_exception() -> None:
    with pytest.raises(DomainError):
        raise DomainError("test")
