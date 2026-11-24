"""BYOK User API Key domain entity (user_api_keys table)."""

from enum import Enum
from typing import Optional
from src.models.v1.base import DomainModel


class KeySource(str, Enum):
    PERSONAL = "PERSONAL"
    SYSTEM = "SYSTEM"
    NONE = "NONE"


class KeyValidationStatus(str, Enum):
    NOT_TESTED = "NOT_TESTED"
    VALID = "VALID"
    INVALID = "INVALID"
    ERROR = "ERROR"


class ProviderCategory(str, Enum):
    LLM = "LLM"
    SEARCH = "SEARCH"


class UserApiKeyEntity(DomainModel):
    """Domain entity mirroring the user_api_keys table (never holds plaintext)."""

    id: str
    user_id: str
    provider: str
    key_ciphertext: str
    key_last4: Optional[str] = None
    key_fingerprint: Optional[str] = None
    validation_status: str = KeyValidationStatus.NOT_TESTED.value
    last_validated_at: Optional[str] = None
    last_error_summary: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
