"""AI Model Repository — isolates all SQL on the models catalog table."""

from typing import Any, Dict, List, Optional
from src.repositories.base import BaseSQLiteRepository


class ModelRepository(BaseSQLiteRepository):
    """Data access layer for AI model catalog with atomic default switching."""

    def list_by_status(self, status_filter: str = "ALL") -> List[Dict[str, Any]]:
        upper = (status_filter or "ALL").upper().strip()
        if upper in ("ACTIVE", "INACTIVE", "ARCHIVED", "DEGRADED"):
            return self._db.query_all(
                "SELECT * FROM models WHERE status = ? ORDER BY is_default DESC, name ASC",
                (upper,),
            )
        return self._db.query_all("SELECT * FROM models ORDER BY is_default DESC, status ASC, name ASC")

    def get_by_id(self, model_id: str) -> Optional[Dict[str, Any]]:
        return self._db.query_one("SELECT * FROM models WHERE id = ?", (model_id,))

    def get_default_active_id(self) -> Optional[str]:
        row = self._db.query_one("SELECT id FROM models WHERE is_default = 1 AND status = 'ACTIVE' LIMIT 1")
        return row["id"] if row else None

    def get_provider(self, model_id: str) -> Optional[str]:
        row = self._db.query_one("SELECT provider FROM models WHERE id = ?", (model_id,))
        return row["provider"] if row else None

    def create(
        self,
        *,
        model_id: str,
        name: str,
        provider: str,
        context_window: int,
        max_tokens: int,
        supports_streaming: bool,
    ) -> Dict[str, Any]:
        with self._db.transaction() as uow:
            uow.execute(
                """
                INSERT INTO models (id, name, provider, status, is_default, context_window, max_tokens, supports_streaming)
                VALUES (?, ?, ?, 'INACTIVE', 0, ?, ?, ?)
                """,
                (model_id, name, provider, context_window, max_tokens, 1 if supports_streaming else 0),
            )
            created = uow.query_one("SELECT * FROM models WHERE id = ?", (model_id,))
        return created or {}

    def search(
        self,
        *,
        q: Optional[str] = None,
        provider: Optional[str] = "ALL",
        status_filter: Optional[str] = "ALL",
        is_default: Optional[bool] = None,
        sort: Optional[str] = "name_asc",
    ) -> List[Dict[str, Any]]:
        sql = "SELECT * FROM models WHERE 1=1"
        params: List[Any] = []

        if q and q.strip():
            kw = f"%{q.strip()}%"
            sql += " AND (name LIKE ? OR id LIKE ?)"
            params.extend([kw, kw])

        if provider and provider.upper() != "ALL":
            sql += " AND LOWER(provider) = ?"
            params.append(provider.lower().strip())

        if status_filter and status_filter.upper() != "ALL":
            sql += " AND status = ?"
            params.append(status_filter.upper().strip())

        if is_default is not None:
            sql += " AND is_default = ?"
            params.append(1 if is_default else 0)

        if sort == "latency_asc":
            sql += " ORDER BY CASE WHEN latency_ms IS NULL THEN 1 ELSE 0 END, latency_ms ASC, name ASC"
        elif sort == "context_desc":
            sql += " ORDER BY context_window DESC, name ASC"
        else:
            sql += " ORDER BY is_default DESC, name ASC"

        return self._db.query_all(sql, tuple(params))

    def set_default_atomic(self, model_id: str) -> None:
        """Atomically clears old default and sets the target model as default."""
        with self._db.transaction() as uow:
            uow.execute("UPDATE models SET is_default = 0")
            uow.execute(
                "UPDATE models SET is_default = 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (model_id,),
            )

    def update_config(
        self,
        *,
        model_id: str,
        name: str,
        context_window: int,
        max_tokens: int,
        supports_streaming: bool,
    ) -> Optional[Dict[str, Any]]:
        with self._db.transaction() as uow:
            uow.execute(
                """
                UPDATE models
                SET name = ?, context_window = ?, max_tokens = ?, supports_streaming = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (name, context_window, max_tokens, 1 if supports_streaming else 0, model_id),
            )
            return uow.query_one("SELECT * FROM models WHERE id = ?", (model_id,))

    def update_status(self, model_id: str, new_status: str) -> None:
        self._db.execute_commit(
            "UPDATE models SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (new_status, model_id),
        )

    def record_latency(self, model_id: str, latency_ms: int) -> None:
        self._db.execute_commit(
            "UPDATE models SET latency_ms = ?, last_checked_at = CURRENT_TIMESTAMP WHERE id = ?",
            (latency_ms, model_id),
        )
