"""Cryptographic secret vault (AES-256-GCM + HKDF-SHA256) with injectable key provider."""

import base64
import hashlib
import logging
import os
from typing import Callable, Optional
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from src.core.config import settings

logger = logging.getLogger("chatjpt.secret_vault")

_VAULT_SALT = b"ai-chan-discord-bot-token-salt-v1"
_VAULT_INFO = b"ai-chan-credential-vault-aes-gcm"


def _default_key_material_provider() -> str:
    raw_key = (
        getattr(settings, "AI_CHAN_SECRET_ENCRYPTION_KEY", "")
        or os.environ.get("AI_CHAN_SECRET_ENCRYPTION_KEY", "")
    )
    if not raw_key:
        raw_key = settings.SECRET_KEY or "ai-chan-default-secure-vault-key"
        if settings.APP_ENV != "development":
            logger.warning("AI_CHAN_SECRET_ENCRYPTION_KEY is unset; deriving vault key from SECRET_KEY.")
    return raw_key


class SecretVault:
    """AES-256-GCM authenticated secret vault with per-key HKDF derivation cache."""

    def __init__(self, key_material_provider: Optional[Callable[[], str]] = None):
        self._key_material_provider = key_material_provider or _default_key_material_provider
        self._cached_raw: Optional[str] = None
        self._cached_key: Optional[bytes] = None

    def _derive_key(self) -> bytes:
        raw_key = self._key_material_provider()
        if self._cached_raw == raw_key and self._cached_key is not None:
            return self._cached_key
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=_VAULT_SALT,
            info=_VAULT_INFO,
        )
        derived = hkdf.derive(raw_key.encode("utf-8"))
        self._cached_raw = raw_key
        self._cached_key = derived
        return derived

    def encrypt(self, plaintext: str) -> str:
        if not plaintext:
            raise ValueError("Cannot encrypt an empty secret.")
        aesgcm = AESGCM(self._derive_key())
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
        return base64.b64encode(nonce + ciphertext).decode("ascii")

    def decrypt(self, ciphertext_b64: str) -> str:
        if not ciphertext_b64:
            raise ValueError("Cannot decrypt an empty ciphertext.")
        try:
            combined = base64.b64decode(ciphertext_b64.encode("ascii"))
            if len(combined) < 28:
                raise ValueError("Invalid ciphertext length.")
            nonce, ciphertext = combined[:12], combined[12:]
            aesgcm = AESGCM(self._derive_key())
            return aesgcm.decrypt(nonce, ciphertext, None).decode("utf-8")
        except Exception as exc:
            raise ValueError("Decryption failed: corrupted credential or invalid encryption key.") from exc

    @staticmethod
    def mask(plaintext: str, visible_suffix_len: int = 4) -> str:
        if not plaintext:
            return ""
        cleaned = plaintext.strip()
        if len(cleaned) <= visible_suffix_len:
            return "*" * len(cleaned)
        return "****" + cleaned[-visible_suffix_len:]

    @staticmethod
    def fingerprint(plaintext: str) -> str:
        if not plaintext:
            return ""
        return hashlib.sha256(plaintext.strip().encode("utf-8")).hexdigest()[:8]


default_vault = SecretVault()


def encrypt_secret(plaintext: str) -> str:
    return default_vault.encrypt(plaintext)


def decrypt_secret(ciphertext_b64: str) -> str:
    return default_vault.decrypt(ciphertext_b64)


def mask_secret(plaintext: str, visible_suffix_len: int = 4) -> str:
    return SecretVault.mask(plaintext, visible_suffix_len=visible_suffix_len)


def get_secret_fingerprint(plaintext: str) -> str:
    return SecretVault.fingerprint(plaintext)
