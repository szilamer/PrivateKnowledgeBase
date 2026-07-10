import mimetypes
import os
from pathlib import Path

from domain.content_hash import compute_file_hash, safe_resolve_path
from domain.sources import Source, SourceType
from domain.sync import DiscoveredObject


class LocalFolderConnector:
    """FR-SRC-001 — discover files in a permitted local directory."""

    async def discover(self, source: Source) -> list[DiscoveredObject]:
        if source.type != SourceType.LOCAL_FOLDER:
            msg = "Source is not a local folder"
            raise ValueError(msg)

        root_path = Path(str(source.configuration.get("path", ""))).expanduser()
        if not root_path.exists() or not root_path.is_dir():
            msg = f"Local path does not exist: {root_path}"
            raise ValueError(msg)

        raw_extensions = source.configuration.get("file_extensions", [".md", ".txt", ".pdf"])
        if not isinstance(raw_extensions, list):
            raw_extensions = [".md", ".txt", ".pdf"]
        extensions = {str(ext).lower() for ext in raw_extensions}
        discovered: list[DiscoveredObject] = []

        for dirpath, _dirnames, filenames in os.walk(root_path):
            for filename in filenames:
                file_path = Path(dirpath) / filename
                if file_path.suffix.lower() not in extensions:
                    continue
                if file_path.is_symlink():
                    continue

                relative = file_path.relative_to(root_path).as_posix()
                safe_resolve_path(root_path, relative)

                content_hash = compute_file_hash(file_path)
                mime_type, _ = mimetypes.guess_type(file_path.name)
                discovered.append(
                    DiscoveredObject(
                        external_id=relative,
                        object_type="file",
                        content_hash=content_hash,
                        mime_type=mime_type,
                        content_ref=str(file_path),
                    )
                )
        return discovered
