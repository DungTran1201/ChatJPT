"""Rule Repository — isolates all SQL on the rules table with atomic OCC updates."""

from typing import Any, Dict, List, Optional, Tuple
from src.repositories.base import BaseSQLiteRepository

_ALLOWED_SORT_FIELDS = {
    "updated_at": "updated_at",
    "created_at": "created_at",
    "name": "name",
    "priority": "priority",
}


class RuleRepository(BaseSQLiteRepository):
    """Data access layer for pedagogical & system rules."""

    def list_paginated(
        self,
        *,
        user_id: str,
        search: Optional[str] = None,
        scope: Optional[str] = "all",
        activation_mode: Optional[str] = None,
        status_filter: Optional[str] = "active",
        page: int = 1,
        limit: int = 20,
        sort_by: str = "updated_at",
        sort_order: str = "desc",
    ) -> Tuple[List[Dict[str, Any]], int]:
        offset = (page - 1) * limit
        conditions = ["deleted_at IS NULL"]
        params: List[Any] = []

        if scope == "user":
            conditions.append("user_id = ? AND scope = 'user'")
            params.append(user_id)
        elif scope == "system":
            conditions.append("scope = 'system'")
        else:
            conditions.append("(user_id = ? OR scope = 'system')")
            params.append(user_id)

        if status_filter and status_filter != "all":
            conditions.append("status = ?")
            params.append(status_filter)

        if activation_mode and activation_mode != "all":
            conditions.append("activation_mode = ?")
            params.append(activation_mode)

        if search and search.strip():
            q = f"%{search.strip()}%"
            conditions.append("(name LIKE ? OR description LIKE ? OR tags LIKE ?)")
            params.extend([q, q, q])

        where_clause = " AND ".join(conditions)
        order_col = _ALLOWED_SORT_FIELDS.get(sort_by, "updated_at")
        order_dir = "ASC" if str(sort_order).lower() == "asc" else "DESC"

        total_row = self._db.query_one(f"SELECT COUNT(*) AS total FROM rules WHERE {where_clause}", tuple(params))
        total = int(total_row["total"]) if total_row else 0

        rows = self._db.query_all(
            f"""
            SELECT * FROM rules
            WHERE {where_clause}
            ORDER BY {order_col} {order_dir}
            LIMIT ? OFFSET ?
            """,
            (*params, limit, offset),
        )
        return rows, total

    def list_active_always_on(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Returns active always_on rules (user + system) ordered by priority DESC for Chat prompt injection."""
        return self._db.query_all(
            """
            SELECT id, name, content, scope, priority
            FROM rules
            WHERE deleted_at IS NULL
              AND status = 'active'
              AND activation_mode = 'always_on'
              AND (user_id = ? OR scope = 'system')
            ORDER BY priority DESC, updated_at DESC
            LIMIT ?
            """,
            (user_id, limit),
        )

    def get_active_by_id(self, rule_id: str) -> Optional[Dict[str, Any]]:
        return self._db.query_one(
            "SELECT * FROM rules WHERE id = ? AND deleted_at IS NULL",
            (rule_id,),
        )

    def exists_name_for_user(
        self,
        user_id: str,
        name: str,
        *,
        exclude_id: Optional[str] = None,
    ) -> bool:
        if exclude_id:
            row = self._db.query_one(
                "SELECT id FROM rules WHERE user_id = ? AND name = ? COLLATE NOCASE AND id != ? AND deleted_at IS NULL",
                (user_id, name, exclude_id),
            )
        else:
            row = self._db.query_one(
                "SELECT id FROM rules WHERE user_id = ? AND name = ? COLLATE NOCASE AND deleted_at IS NULL",
                (user_id, name),
            )
        return row is not None

    def create(self, record: Dict[str, Any]) -> None:
        self._db.execute_commit(
            """
            INSERT INTO rules (
                id, user_id, name, description, content,
                scope, activation_mode, glob_patterns, tags,
                priority, status, version, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, 'user', ?, ?, ?, ?, 'active', 1, ?, ?)
            """,
            (
                record["id"],
                record["user_id"],
                record["name"],
                record.get("description"),
                record["content"],
                record["activation_mode"],
                record["glob_patterns"],
                record["tags"],
                record["priority"],
                record["created_at"],
                record["updated_at"],
            ),
        )

    def update_with_occ(
        self,
        *,
        rule_id: str,
        user_id: str,
        expected_version: int,
        fields: Dict[str, Any],
    ) -> int:
        """Atomic Optimistic Concurrency Control update (prevents TOCTOU lost updates)."""
        return self._db.execute_commit(
            """
            UPDATE rules SET
                name = ?,
                description = ?,
                content = ?,
                activation_mode = ?,
                glob_patterns = ?,
                tags = ?,
                priority = ?,
                status = ?,
                version = version + 1,
                updated_at = ?
            WHERE id = ? AND user_id = ? AND version = ? AND deleted_at IS NULL
            """,
            (
                fields["name"],
                fields["description"],
                fields["content"],
                fields["activation_mode"],
                fields["glob_patterns"],
                fields["tags"],
                fields["priority"],
                fields["status"],
                fields["updated_at"],
                rule_id,
                user_id,
                expected_version,
            ),
        )

    def update_status(self, rule_id: str, user_id: str, new_status: str, updated_at: str) -> None:
        self._db.execute_commit(
            "UPDATE rules SET status = ?, updated_at = ? WHERE id = ? AND user_id = ? AND deleted_at IS NULL",
            (new_status, updated_at, rule_id, user_id),
        )

    def soft_delete(self, rule_id: str, user_id: str, deleted_at: str) -> None:
        self._db.execute_commit(
            "UPDATE rules SET deleted_at = ?, status = 'archived' WHERE id = ? AND user_id = ?",
            (deleted_at, rule_id, user_id),
        )
