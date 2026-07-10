import hashlib
from pathlib import Path


def compute_content_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def compute_file_hash(path: Path) -> str:
    return compute_content_hash(path.read_bytes())


def safe_resolve_path(root: Path, relative: str) -> Path:
    """Resolve a path and ensure it stays within root (FR-SRC-001 path traversal protection)."""
    root_resolved = root.resolve()
    candidate = (root_resolved / relative).resolve()
    if not str(candidate).startswith(str(root_resolved)):
        msg = f"Path escapes configured root: {relative}"
        raise ValueError(msg)
    return candidate
