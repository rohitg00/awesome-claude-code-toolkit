"""At-rest encryption for secret fields (API keys, key numbers, passwords).

Secrets are stored as Fernet tokens (AES-128-CBC + HMAC) prefixed with
``enc:v1:`` so the layer is self-describing and back-compatible: any value that
is *not* prefixed is treated as plaintext on read (eases manual seeding and
migration). The symmetric key comes from ``NTXP_APILOG_KEY`` or an
auto-generated key file with 0600 permissions.

The point of encryption here is defense in depth — the shared ``.db`` file is
never committed, but a stray copy/backup of it should not leak live keys. It is
*not* a substitute for filesystem permissions on the key and DB.
"""
from __future__ import annotations

import os

from .config import key_path

_PREFIX = "enc:v1:"


class CryptoUnavailable(RuntimeError):
    """Raised when the `cryptography` package is missing."""


def _load_fernet():
    try:
        from cryptography.fernet import Fernet
    except Exception as exc:  # pragma: no cover - import guard
        raise CryptoUnavailable(
            "The 'cryptography' package is required for secret storage. "
            "Install with: pip install 'ntxp-apilog' (it is a core dependency)."
        ) from exc
    return Fernet


def _key_material() -> bytes:
    """Resolve the Fernet key: env var > key file (generated on first use)."""
    env = os.environ.get("NTXP_APILOG_KEY")
    if env:
        return env.strip().encode("utf-8")

    Fernet = _load_fernet()
    p = key_path()
    if p.exists():
        return p.read_text(encoding="utf-8").strip().encode("utf-8")

    # First run: mint a key and persist it with restrictive perms.
    p.parent.mkdir(parents=True, exist_ok=True)
    key = Fernet.generate_key()
    p.write_bytes(key)
    try:
        os.chmod(p, 0o600)
    except OSError:  # pragma: no cover - platform dependent (e.g. Windows)
        pass
    return key


class Cipher:
    """Encrypt/decrypt/mask helpers. Cheap to construct; caches the Fernet."""

    def __init__(self) -> None:
        Fernet = _load_fernet()
        self._f = Fernet(_key_material())

    def encrypt(self, value: str | None) -> str | None:
        """Encrypt a non-empty string; pass through None/empty unchanged."""
        if not value:
            return value
        token = self._f.encrypt(value.encode("utf-8")).decode("ascii")
        return _PREFIX + token

    def decrypt(self, stored: str | None) -> str | None:
        """Decrypt a stored value. Non-prefixed values are returned verbatim."""
        if not stored:
            return stored
        if not stored.startswith(_PREFIX):
            return stored  # legacy/plaintext
        token = stored[len(_PREFIX):].encode("ascii")
        return self._f.decrypt(token).decode("utf-8")


def is_encrypted(stored: str | None) -> bool:
    return bool(stored) and stored.startswith(_PREFIX)


def mask(secret: str | None, show: int = 4) -> str:
    """Render a secret for display: keep the last ``show`` chars, dot the rest."""
    if not secret:
        return ""
    if len(secret) <= show:
        return "•" * len(secret)
    return "•" * (len(secret) - show) + secret[-show:]


def generate_key() -> str:
    """Mint a fresh Fernet key (for `NTXP_APILOG_KEY` or the key file)."""
    Fernet = _load_fernet()
    return Fernet.generate_key().decode("ascii")
