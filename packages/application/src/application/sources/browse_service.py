import os
from pathlib import Path

from domain.errors import DomainError
from domain.local_browse import LocalBrowseResult, LocalFolderEntry

_BLOCKED_SEGMENTS = {
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
}

_SYSTEM_PREFIXES = (
    "/System",
    "/private/var",
    "/proc",
    "/sys",
    "/dev",
)


class HostPathMapper:
    """Map display paths (~/Projects) to container host mount (/host/Projects)."""

    def __init__(self, host_root: str) -> None:
        self._host_root = Path(host_root).resolve() if host_root else None

    def to_filesystem(self, display_path: str) -> Path:
        raw = display_path.strip() or "~"
        if raw == "~":
            if self._host_root is not None:
                return self._host_root
            return Path.home()

        expanded = Path(raw).expanduser()
        if self._host_root is None:
            return expanded.resolve()

        if raw.startswith("~/") or raw == "~":
            suffix = raw[2:] if raw.startswith("~/") else ""
            candidate = self._host_root if not suffix else self._host_root / suffix
            return candidate.resolve()

        candidate = Path(raw)
        if not candidate.is_absolute():
            candidate = self._host_root / raw
        resolved = candidate.resolve()
        if not str(resolved).startswith(str(self._host_root)):
            msg = f"Path is outside allowed host root: {display_path}"
            raise DomainError(msg)
        return resolved

    def to_display(self, fs_path: Path) -> str:
        resolved = fs_path.resolve()
        if self._host_root is not None:
            try:
                relative = resolved.relative_to(self._host_root)
                return "~" if not relative.parts else f"~/{relative.as_posix()}"
            except ValueError:
                return str(resolved)
        home = Path.home()
        try:
            relative = resolved.relative_to(home)
            return "~" if not relative.parts else f"~/{relative.as_posix()}"
        except ValueError:
            return str(resolved)


class LocalFolderBrowseService:
    """FR-SRC-011 / UI-7b — browse host folders for local source connection."""

    def __init__(self, host_root: str = "/host") -> None:
        self._mapper = HostPathMapper(host_root)

    def browse(self, display_path: str | None = None) -> LocalBrowseResult:
        target_display = (display_path or "~").strip() or "~"
        try:
            fs_path = self._mapper.to_filesystem(target_display)
        except DomainError as exc:
            return LocalBrowseResult(
                path=target_display,
                can_select=False,
                readable=False,
                error=str(exc),
            )

        if not fs_path.exists():
            return LocalBrowseResult(
                path=target_display,
                can_select=False,
                readable=False,
                error=f"A mappa nem található: {target_display}",
            )
        if not fs_path.is_dir():
            return LocalBrowseResult(
                path=target_display,
                can_select=False,
                readable=False,
                error=f"Nem mappa: {target_display}",
            )
        if not os.access(fs_path, os.R_OK | os.X_OK):
            return LocalBrowseResult(
                path=target_display,
                can_select=False,
                readable=False,
                error="Nincs olvasási jogosultság ehhez a mappához.",
            )
        if _is_blocked_system_path(fs_path, self._mapper._host_root):
            return LocalBrowseResult(
                path=target_display,
                can_select=False,
                readable=False,
                error="Ez a rendszermappa nem választható ki.",
            )

        parent_display: str | None = None
        if target_display not in {"~", "/"}:
            parent_fs = fs_path.parent
            parent_display = self._mapper.to_display(parent_fs)

        entries: list[LocalFolderEntry] = []
        try:
            for child in sorted(fs_path.iterdir(), key=lambda item: item.name.lower()):
                if not child.is_dir() or child.is_symlink():
                    continue
                if child.name in _BLOCKED_SEGMENTS or child.name.startswith("."):
                    continue
                if _is_blocked_system_path(child, self._mapper._host_root):
                    continue
                if not os.access(child, os.R_OK | os.X_OK):
                    continue
                child_display = self._mapper.to_display(child)
                entries.append(
                    LocalFolderEntry(
                        name=child.name,
                        path=child_display,
                        has_children=_directory_has_subdirs(child),
                    )
                )
        except OSError as exc:
            return LocalBrowseResult(
                path=target_display,
                parent_path=parent_display,
                can_select=True,
                readable=False,
                error=f"Nem sikerült beolvasni a mappa tartalmát: {exc}",
            )

        return LocalBrowseResult(
            path=target_display,
            parent_path=parent_display,
            entries=entries,
            can_select=True,
            readable=True,
        )

    def validate_selectable(self, display_path: str) -> None:
        result = self.browse(display_path)
        if result.error or not result.can_select:
            raise DomainError(result.error or f"Invalid folder: {display_path}")
        if not result.readable:
            raise DomainError(f"Folder is not readable: {display_path}")


def _is_blocked_system_path(path: Path, allowed_root: Path | None = None) -> bool:
    resolved = path.resolve()
    if allowed_root is not None:
        try:
            resolved.relative_to(allowed_root.resolve())
            return False
        except ValueError:
            pass
    normalized = str(resolved)
    return any(normalized.startswith(prefix) for prefix in _SYSTEM_PREFIXES)


def _directory_has_subdirs(path: Path) -> bool:
    try:
        for child in path.iterdir():
            if (
                child.is_dir()
                and not child.is_symlink()
                and child.name not in _BLOCKED_SEGMENTS
                and not child.name.startswith(".")
                and os.access(child, os.R_OK | os.X_OK)
            ):
                return True
    except OSError:
        return False
    return False
