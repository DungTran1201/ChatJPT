"""Credential and BYOK API Key Service (SRP, DIP, Strategy via ProviderRegistry).

Preserves classmethod compatibility for existing tests & callers while allowing full
constructor dependency injection of ApiKeyRepository, SecretVault, EnvFileStore, and ProviderRegistry.
"""

import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.core.config import settings
from src.core.secret_vault import SecretVault, default_vault
from src.repositories.api_key_repo import ApiKeyRepository
from src.services.env_file_store import EnvFileStore
from src.services.provider_registry import (
    ALLOWLISTED_SYSTEM_ENV_VARS,
    SUPPORTED_PROVIDERS,
    ProviderRegistry,
    canonicalize_provider,
    provider_registry,
    redact_secrets_from_text,
    validate_ollama_url,
)

logger = logging.getLogger("credential_service")


class CredentialService:
    """Manages user-scoped encrypted credentials with fallback to system .env."""

    def __init__(
        self,
        repo: Optional[ApiKeyRepository] = None,
        vault: Optional[SecretVault] = None,
        env_store: Optional[EnvFileStore] = None,
        registry: Optional[ProviderRegistry] = None,
    ):
        self._repo = repo or ApiKeyRepository()
        self._vault = vault or default_vault
        self._env_store = env_store or EnvFileStore()
        self._registry = registry or provider_registry

    def resolve_system_key(self, provider: str) -> Optional[str]:
        spec = self._registry.get(provider)
        if not spec:
            return None
        val = getattr(settings, spec.env_var, None)
        if val and str(val).strip():
            return str(val).strip()
        env_val = os.getenv(spec.env_var, "")
        if env_val and env_val.strip():
            return env_val.strip()
        for alias_env in spec.env_aliases:
            alt = os.getenv(alias_env, "").strip()
            if alt:
                return alt
        return None

    def resolve_effective_key(self, user_id: Optional[str], provider: str) -> Optional[str]:
        spec = self._registry.get(provider)
        if not spec:
            return None

        if user_id:
            ciphertext = self._repo.get_active_ciphertext(user_id, spec.id)
            if ciphertext:
                try:
                    decrypted = self._vault.decrypt(ciphertext)
                    if decrypted and decrypted.strip():
                        return decrypted.strip()
                except Exception as err:
                    logger.error("Failed to decrypt personal key for user %s, provider %s: %s", user_id, spec.id, err)

        return self.resolve_system_key(spec.id)

    def check_provider_configured(self, provider: str, user_id: Optional[str] = None) -> bool:
        key = self.resolve_effective_key(user_id, provider)
        return bool(key and key.strip())

    def list_user_keys_status(self, user_id: str) -> List[Dict[str, Any]]:
        personal_rows = self._repo.list_status_by_user(user_id)
        personal_by_prov = {r["provider"]: r for r in personal_rows}

        results = []
        for spec in self._registry.all_specs():
            system_key = self.resolve_system_key(spec.id)
            has_system = bool(system_key and system_key.strip())
            personal_row = personal_by_prov.get(spec.id)
            has_personal = bool(personal_row and personal_row.get("is_active"))

            if has_personal:
                source = "PERSONAL"
                is_configured = True
                masked_hint = f"****{personal_row['key_last4']}" if personal_row.get("key_last4") else "Configured"
                val_status = personal_row.get("validation_status") or "NOT_TESTED"
                last_tested = personal_row.get("last_validated_at")
                last_error = personal_row.get("last_error_summary")
                updated_at = personal_row.get("updated_at")
            elif has_system:
                source = "SYSTEM"
                is_configured = True
                masked_hint = self._vault.mask(system_key) if spec.is_secret else system_key
                val_status = "NOT_TESTED"
                last_tested = None
                last_error = None
                updated_at = None
            else:
                source = "NONE"
                is_configured = False
                masked_hint = ""
                val_status = "NOT_TESTED"
                last_tested = None
                last_error = None
                updated_at = None

            results.append(
                {
                    "provider": spec.id,
                    "name": spec.name,
                    "category": spec.category,
                    "env_var": spec.env_var,
                    "description": spec.description,
                    "doc_url": spec.doc_url,
                    "placeholder": spec.placeholder,
                    "is_secret": spec.is_secret,
                    "is_configured": is_configured,
                    "source": source,
                    "masked_hint": masked_hint,
                    "has_personal_key": has_personal,
                    "has_system_key": has_system,
                    "validation_status": val_status,
                    "last_validated_at": last_tested,
                    "last_error_summary": last_error,
                    "updated_at": updated_at,
                    "requires_restart": False,
                }
            )
        return results

    def save_user_key(self, user_id: str, provider: str, raw_key: str) -> Dict[str, Any]:
        spec = self._registry.get(provider)
        if not spec:
            raise ValueError(f"Nhà cung cấp '{provider}' không được hỗ trợ trong danh mục allowlist.")

        key_clean = (raw_key or "").strip()
        if not key_clean:
            raise ValueError("Khóa API không được để trống. Để xóa khóa, hãy dùng thao tác Reset/Delete.")
        if len(key_clean) < 3:
            raise ValueError("Độ dài khóa API không hợp lệ (tối thiểu 3 ký tự).")
        if len(key_clean) > 500:
            raise ValueError("Độ dài khóa API vượt quá giới hạn an toàn (tối đa 500 ký tự).")
        if spec.id == "ollama":
            key_clean = validate_ollama_url(key_clean)

        ciphertext = self._vault.encrypt(key_clean)
        last4 = key_clean[-4:] if len(key_clean) >= 4 else key_clean
        fingerprint = self._vault.fingerprint(key_clean)
        self._repo.upsert(
            user_id=user_id,
            provider=spec.id,
            ciphertext=ciphertext,
            last4=last4,
            fingerprint=fingerprint,
        )

        logger.info("User %s stored encrypted credential for provider %s.", user_id, spec.id)
        return {
            "provider": spec.id,
            "is_configured": True,
            "source": "PERSONAL",
            "masked_hint": f"****{last4}",
            "validation_status": "NOT_TESTED",
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    def remove_user_key(self, user_id: str, provider: str) -> Dict[str, Any]:
        spec = self._registry.get(provider)
        if not spec:
            raise ValueError(f"Nhà cung cấp '{provider}' không được hỗ trợ trong danh mục allowlist.")

        self._repo.delete(user_id, spec.id)
        system_key = self.resolve_system_key(spec.id)
        has_system = bool(system_key and system_key.strip())

        logger.info("User %s removed personal credential for provider %s.", user_id, spec.id)
        return {
            "provider": spec.id,
            "is_configured": has_system,
            "source": "SYSTEM" if has_system else "NONE",
            "masked_hint": (
                self._vault.mask(system_key)
                if (has_system and spec.is_secret)
                else (system_key if has_system else "")
            ),
            "has_system_key": has_system,
            "validation_status": "NOT_TESTED",
        }

    async def probe_connection(
        self,
        provider: str,
        user_id: Optional[str] = None,
        candidate_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        spec = self._registry.get(provider)
        if not spec:
            raise ValueError(f"Nhà cung cấp '{provider}' không được hỗ trợ trong danh mục allowlist.")

        testing_candidate = bool(candidate_key and candidate_key.strip())
        effective_key = (candidate_key or "").strip() if testing_candidate else (self.resolve_effective_key(user_id, spec.id) or "")
        if not effective_key:
            raise ValueError(f"Chưa có cấu hình khóa API cho nhà cung cấp {spec.name}.")

        start_time = time.perf_counter()
        tested_at_str = datetime.now(timezone.utc).isoformat()
        status_result = "VALID"
        error_summary: Optional[str] = None

        try:
            await self._registry.probe(spec.id, effective_key)
            latency_ms = max(1, int((time.perf_counter() - start_time) * 1000))
        except Exception as exc:
            raw_err = str(exc)
            latency_ms = max(1, int((time.perf_counter() - start_time) * 1000))
            error_summary = redact_secrets_from_text(raw_err, [effective_key])
            status_result = (
                "INVALID"
                if any(w in raw_err.lower() for w in ("401", "403", "unauthorized", "invalid", "api_key_invalid"))
                else "ERROR"
            )

        # Only persist validation status when validating the user's saved personal key (not unsaved candidate).
        if user_id and not testing_candidate and self._repo.get_active_ciphertext(user_id, spec.id):
            self._repo.record_validation_result(
                user_id=user_id,
                provider=spec.id,
                validation_status=status_result,
                error_summary=error_summary,
            )

        if status_result == "VALID":
            return {
                "healthy": True,
                "provider": spec.id,
                "latency_ms": latency_ms,
                "validation_status": "VALID",
                "message": f"Kết nối thành công với {spec.name} (độ trễ {latency_ms}ms).",
                "tested_at": tested_at_str,
            }
        return {
            "healthy": False,
            "provider": spec.id,
            "latency_ms": latency_ms,
            "validation_status": status_result,
            "message": f"Kiểm tra kết nối thất bại: {error_summary}",
            "tested_at": tested_at_str,
        }

    def update_system_env(self, env_var: str, new_value: str) -> Dict[str, Any]:
        return self._env_store.update_variable(env_var, new_value)

    # ------------------------------------------------------------------
    # Backward-compatible classmethod facade for legacy callers & tests
    # ------------------------------------------------------------------
    @staticmethod
    def get_system_key(provider: str) -> Optional[str]:
        return _default_credential_service.resolve_system_key(provider)

    @classmethod
    def get_effective_key(cls, user_id: Optional[str], provider: str) -> Optional[str]:
        return _default_credential_service.resolve_effective_key(user_id, provider)

    @classmethod
    def is_provider_configured(cls, provider: str, user_id: Optional[str] = None) -> bool:
        return _default_credential_service.check_provider_configured(provider, user_id=user_id)

    @classmethod
    def get_user_keys_status(cls, user_id: str) -> List[Dict[str, Any]]:
        return _default_credential_service.list_user_keys_status(user_id)

    @classmethod
    def set_user_key(cls, user_id: str, provider: str, raw_key: str) -> Dict[str, Any]:
        return _default_credential_service.save_user_key(user_id, provider, raw_key)

    @classmethod
    def delete_user_key(cls, user_id: str, provider: str) -> Dict[str, Any]:
        return _default_credential_service.remove_user_key(user_id, provider)

    @classmethod
    async def validate_connection(
        cls,
        provider: str,
        user_id: Optional[str] = None,
        candidate_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        return await _default_credential_service.probe_connection(
            provider=provider,
            user_id=user_id,
            candidate_key=candidate_key,
        )

    @classmethod
    def update_system_env_variable(cls, env_var: str, new_value: str) -> Dict[str, Any]:
        return _default_credential_service.update_system_env(env_var, new_value)


_default_credential_service = CredentialService()

__all__ = [
    "SUPPORTED_PROVIDERS",
    "ALLOWLISTED_SYSTEM_ENV_VARS",
    "canonicalize_provider",
    "redact_secrets_from_text",
    "CredentialService",
]
