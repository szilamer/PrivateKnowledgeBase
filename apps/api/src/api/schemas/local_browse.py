from pydantic import BaseModel, Field


class LocalFolderEntryResponse(BaseModel):
    name: str
    path: str
    has_children: bool


class LocalBrowseResponse(BaseModel):
    path: str
    parent_path: str | None = None
    entries: list[LocalFolderEntryResponse] = Field(default_factory=list)
    can_select: bool = True
    readable: bool = True
    error: str | None = None
