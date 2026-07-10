from typing import Annotated, Literal

from pydantic import BaseModel, Field, model_validator


class SyncConfig(BaseModel):
    on_startup: bool = True
    interval_minutes: int = 60


class LocalFolderSourceConfig(BaseModel):
    id: str
    type: Literal["local_folder"] = "local_folder"
    name: str
    enabled: bool = True
    paths: list[str] = Field(min_length=1)
    include_extensions: list[str] = Field(default_factory=lambda: [".md", ".txt", ".pdf"])
    exclude_globs: list[str] = Field(default_factory=lambda: ["**/node_modules/**", "**/.git/**"])


class GoogleDriveSourceConfig(BaseModel):
    id: str
    type: Literal["google_drive"] = "google_drive"
    name: str
    enabled: bool = True
    account: str = "google:primary"
    folder_ids: list[str] = Field(default_factory=list)
    include_google_docs: bool = True
    include_extensions: list[str] = Field(default_factory=lambda: [".md", ".txt", ".pdf"])


class GmailSourceConfig(BaseModel):
    id: str
    type: Literal["gmail"] = "gmail"
    name: str
    enabled: bool = True
    account: str = "google:primary"
    query: str = "label:important newer_than:365d"
    label_ids: list[str] = Field(default_factory=list)
    include_attachments: bool = True
    attachment_extensions: list[str] = Field(default_factory=lambda: [".pdf", ".txt", ".md"])


class GoogleCalendarSourceConfig(BaseModel):
    id: str
    type: Literal["google_calendar"] = "google_calendar"
    name: str
    enabled: bool = True
    account: str = "google:primary"
    calendar_ids: list[str] = Field(default_factory=lambda: ["primary"])
    horizon_past_days: int = 365
    horizon_future_days: int = 90


SourceEntryConfig = Annotated[
    LocalFolderSourceConfig
    | GoogleDriveSourceConfig
    | GmailSourceConfig
    | GoogleCalendarSourceConfig,
    Field(discriminator="type"),
]


class SourcesFileConfig(BaseModel):
    version: str = "1"
    sync: SyncConfig = Field(default_factory=SyncConfig)
    sources: list[SourceEntryConfig] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_unique_ids(self) -> "SourcesFileConfig":
        ids = [entry.id for entry in self.sources]
        if len(ids) != len(set(ids)):
            msg = "Duplicate source id in sources.yaml"
            raise ValueError(msg)
        return self
