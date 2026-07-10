from pydantic import BaseModel, Field


class LocalFolderEntry(BaseModel):
    name: str
    path: str
    has_children: bool = True


class LocalBrowseResult(BaseModel):
    path: str
    parent_path: str | None = None
    entries: list[LocalFolderEntry] = Field(default_factory=list)
    can_select: bool = True
    readable: bool = True
    error: str | None = None
