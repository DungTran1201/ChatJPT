"""Backward-compatibility re-export shim for src.schemas.v1.api_keys."""

from src.schemas.v1.api_keys import (
    ProviderKeyStatusResponse,
    SetApiKeyRequest,
    TestApiKeyRequest,
    TestApiKeyResponse,
    UpdateSystemEnvRequest,
)

__all__ = [
    "ProviderKeyStatusResponse",
    "SetApiKeyRequest",
    "TestApiKeyRequest",
    "TestApiKeyResponse",
    "UpdateSystemEnvRequest",
]
