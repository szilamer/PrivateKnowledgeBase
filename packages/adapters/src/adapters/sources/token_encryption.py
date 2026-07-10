import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken


def _derive_key(secret: str) -> bytes:
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


class TokenEncryption:
    """ADR-013 — encrypt connector refresh tokens at rest."""

    def __init__(self, secret: str) -> None:
        self._fernet = Fernet(_derive_key(secret))

    def encrypt(self, value: str) -> str:
        return self._fernet.encrypt(value.encode("utf-8")).decode("utf-8")

    def decrypt(self, value: str) -> str:
        try:
            return self._fernet.decrypt(value.encode("utf-8")).decode("utf-8")
        except InvalidToken as exc:
            msg = "Failed to decrypt connector credential"
            raise ValueError(msg) from exc
