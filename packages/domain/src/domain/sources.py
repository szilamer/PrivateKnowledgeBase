from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field


class SourceType(StrEnum):
    LOCAL_FOLDER = "local_folder"
    GITHUB = "github"
    GOOGLE_DRIVE = "google_drive"
    GMAIL = "gmail"
    GOOGLE_CALENDAR = "google_calendar"


SOURCE_CONFIG_NAMESPACE = UUID("00000000-0000-4000-8000-000000000101")


def source_id_for_config(config_id: str) -> UUID:
    from uuid import uuid5

    return uuid5(SOURCE_CONFIG_NAMESPACE, config_id)


class Source(BaseModel):
    id: UUID
    type: SourceType
    name: str
    owner_id: UUID
    configuration: dict[str, object] = Field(default_factory=dict)
    enabled: bool = True
    default_project_id: UUID | None = None


class RegisterLocalSourceCommand(BaseModel):
    name: str
    path: str = ""
    paths: list[str] = Field(default_factory=list)
    file_extensions: list[str] = Field(default_factory=lambda: [".md", ".txt", ".pdf"])
    exclude_globs: list[str] = Field(default_factory=lambda: ["**/node_modules/**", "**/.git/**"])
    default_project_id: UUID | None = None
    enabled: bool = True


class RegisterGitHubSourceCommand(BaseModel):
    name: str
    owner: str
    repo: str
    branch: str = "main"
    token_env_var: str = "GITHUB_TOKEN"
    default_project_id: UUID | None = None
    enabled: bool = True
