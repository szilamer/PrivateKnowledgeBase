import pytest
from domain.content_hash import compute_content_hash, safe_resolve_path


def test_compute_content_hash_is_stable() -> None:
    content = b"hello knowledge base"
    assert compute_content_hash(content) == compute_content_hash(content)
    assert len(compute_content_hash(content)) == 64


def test_safe_resolve_path_blocks_traversal(tmp_path: object) -> None:
    from pathlib import Path

    root = Path(str(tmp_path))
    (root / "allowed.txt").write_text("ok", encoding="utf-8")

    resolved = safe_resolve_path(root, "allowed.txt")
    assert resolved.name == "allowed.txt"

    with pytest.raises(ValueError, match="escapes"):
        safe_resolve_path(root, "../outside.txt")
