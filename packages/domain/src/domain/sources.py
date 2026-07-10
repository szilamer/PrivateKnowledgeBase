from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field


class SourceType(StrEnum):
    LOCAL_FOLDER = "local_folder"
    GITHUB = "github"


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
    path: str
    file_extensions: list[str] = Field(default_factory=lambda: [".md", ".txt", ".pdf"])
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
