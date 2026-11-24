"""API Key Repository — isolates all SQL on user_api_keys table."""

import uuid
from typing import Any, Dict, List, Optional
from src.repositories.base import BaseSQLiteRepository


class ApiKeyRepository(BaseSQLiteRepository):
    """Data access layer for encrypted per-user provider API keys."""

    def get_active_ciphertext(self, user_id: str, provider: str) -> Optional[str]:
        row = self._db.query_one(
            """
            SELECT key_ciphertext FROM user_api_keys
            WHERE user_id = ? AND provider = ? AND is_active = 1
            """,
            (user_id, provider),
        )
        return row["key_ciphertext"] if row and row.get("key_ciphertext") else None

    def list_status_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        return self._db.query_all(
            """
            SELECT provider, key_last4, validation_status, last_validated_at,
                   last_error_summary, is_active, updated_at
            FROM user_api_keys
            WHERE user_id = ?
            """,
            (user_id,),
        )

    def upsert(
        self,
        *,
        user_id: str,
        provider: str,
        ciphertext: str,
        last4: str,
        fingerprint: str,
    ) -> str:
        with self._db.transaction() as uow:
            existing = uow.query_one(
                "SELECT id FROM user_api_keys WHERE user_id = ? AND provider = ?",
                (user_id, provider),
            )
            if existing:
                uow.execute(
                    """
                    UPDATE user_api_keys
                    SET key_ciphertext = ?, key_last4 = ?, key_fingerprint = ?,
                        validation_status = 'NOT_TESTED', last_error_summary = NULL,
                        is_active = 1, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ? AND provider = ?
                    """,
                    (ciphertext, last4, fingerprint, user_id, provider),
                )
                return existing["id"]

            key_id = str(uuid.uuid4())
            uow.execute(
                """
                INSERT INTO user_api_keys (
                    id, user_id, provider, key_ciphertext, key_last4, key_fingerprint,
                    validation_status, is_active, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, 'NOT_TESTED', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """,
                (key_id, user_id, provider, ciphertext, last4, fingerprint),
            )
            return key_id

    def delete(self, user_id: str, provider: str) -> None:
        self._db.execute_commit(
            "DELETE FROM user_api_keys WHERE user_id = ? AND provider = ?",
            (user_id, provider),
        )

    def record_validation_result(
        self,
        *,
        user_id: str,
        provider: str,
        validation_status: str,
        error_summary: Optional[str],
    ) -> None:
        self._db.execute_commit(
            """
            UPDATE user_api_keys
            SET validation_status = ?, last_validated_at = CURRENT_TIMESTAMP, last_error_summary = ?
            WHERE user_id = ? AND provider = ?
            """,
            (validation_status, error_summary, user_id, provider),
        )
