import fnmatch
import mimetypes
import os
from pathlib import Path

from domain.content_hash import compute_file_hash, safe_resolve_path
from domain.sources import Source, SourceType
from domain.sync import DiscoveredObject


class LocalFolderConnector:
    """FR-SRC-001 / FR-SRC-011 — discover files in permitted local directories."""

    async def discover(self, source: Source) -> list[DiscoveredObject]:
        if source.type != SourceType.LOCAL_FOLDER:
            msg = "Source is not a local folder"
            raise ValueError(msg)

        roots = _resolve_roots(source)
        raw_extensions = source.configuration.get("file_extensions", [".md", ".txt", ".pdf"])
        if not isinstance(raw_extensions, list):
            raw_extensions = [".md", ".txt", ".pdf"]
        extensions = {str(ext).lower() for ext in raw_extensions}

        exclude_globs = source.configuration.get("exclude_globs", [])
        if not isinstance(exclude_globs, list):
            exclude_globs = []

        discovered: list[DiscoveredObject] = []
        for root_index, root_path in enumerate(roots):
            if not root_path.exists() or not root_path.is_dir():
                msg = f"Local path does not exist: {root_path}"
                raise ValueError(msg)

            prefix = f"{root_index}/" if len(roots) > 1 else ""
            for dirpath, dirnames, filenames in os.walk(root_path):
                dirnames[:] = [
                    name
                    for name in dirnames
                    if not _matches_any_glob(f"{dirpath}/{name}", exclude_globs)
                ]
                for filename in filenames:
                    file_path = Path(dirpath) / filename
                    relative = file_path.relative_to(root_path).as_posix()
                    full_relative = f"{prefix}{relative}"
                    if _matches_any_glob(full_relative, exclude_globs):
                        continue
                    if file_path.suffix.lower() not in extensions:
                        continue
                    if file_path.is_symlink():
                        continue

                    safe_resolve_path(root_path, relative)
                    content_hash = compute_file_hash(file_path)
                    mime_type, _ = mimetypes.guess_type(file_path.name)
                    discovered.append(
                        DiscoveredObject(
                            external_id=full_relative,
                            object_type="file",
                            content_hash=content_hash,
                            mime_type=mime_type,
                            content_ref=str(file_path),
                        )
                    )
        return discovered


def _resolve_roots(source: Source) -> list[Path]:
    paths = source.configuration.get("paths")
    if isinstance(paths, list) and paths:
        return [Path(str(item)).expanduser() for item in paths]
    single = str(source.configuration.get("path", "")).strip()
    if single:
        return [Path(single).expanduser()]
    return []


def _matches_any_glob(path: str, globs: list[object]) -> bool:
    normalized = path.replace("\\", "/")
    return any(fnmatch.fnmatch(normalized, str(pattern)) for pattern in globs)
