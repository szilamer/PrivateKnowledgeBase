import json
import os
from contextlib import suppress
from pathlib import Path


def load_llm_api_key(secrets_path: Path) -> str:
    if not secrets_path.is_file():
        return ""
    try:
        data = json.loads(secrets_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ""
    if not isinstance(data, dict):
        return ""
    value = data.get("api_key", "")
    return str(value).strip() if value else ""


def save_llm_api_key(secrets_path: Path, api_key: str) -> None:
    secrets_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"api_key": api_key.strip()}
    secrets_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    with suppress(OSError):
        os.chmod(secrets_path, 0o600)


def clear_llm_api_key(secrets_path: Path) -> None:
    if secrets_path.is_file():
        secrets_path.unlink()


def api_key_preview(api_key: str) -> str | None:
    if not api_key:
        return None
    if len(api_key) <= 8:
        return "••••••••"
    return f"••••{api_key[-4:]}"
