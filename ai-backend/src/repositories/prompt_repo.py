"""System Prompt / Sensei Repository — isolates all SQL on system_prompts."""

from typing import Any, Dict, List, Optional
from src.repositories.base import BaseSQLiteRepository

_SORT_CLAUSES = {
    "level_asc": "CASE japanese_level WHEN 'N5' THEN 1 WHEN 'N4' THEN 2 WHEN 'N3' THEN 3 WHEN 'N2' THEN 4 WHEN 'N1' THEN 5 ELSE 6 END, updated_at DESC",
    "updated_desc": "updated_at DESC",
    "name_asc": "name COLLATE NOCASE ASC",
    "length_desc": "LENGTH(content) DESC",
}


class PromptRepository(BaseSQLiteRepository):
    """Data access layer for Sensei personas / system prompts."""

    def list_visible(
        self,
        *,
        user_id: str,
        q: Optional[str] = None,
        level: Optional[str] = None,
        sort: str = "level_asc",
    ) -> List[Dict[str, Any]]:
        order_by = _SORT_CLAUSES.get(sort, _SORT_CLAUSES["level_asc"])
        conditions = ["(user_id = ? OR is_system_preset = 1)"]
        params: List[Any] = [user_id]

        if level and level.upper() != "ALL":
            conditions.append("japanese_level = ?")
            params.append(level.upper())

        if q and q.strip():
            pattern = f"%{q.strip()}%"
            conditions.append("(name LIKE ? OR description LIKE ? OR personality LIKE ? OR teaching_style LIKE ?)")
            params.extend([pattern, pattern, pattern, pattern])

        where_clause = " AND ".join(conditions)
        return self._db.query_all(
            f"""
            SELECT id, name, description, LENGTH(content) AS content_length,
                   age, gender, japanese_level, personality, teaching_style, catchphrase,
                   hobbies, avatar_url, voice_id, is_default, is_system_preset, created_at, updated_at
            FROM system_prompts
            WHERE {where_clause}
            ORDER BY {order_by}
            """,
            tuple(params),
        )

    def get_visible(self, prompt_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        return self._db.query_one(
            "SELECT * FROM system_prompts WHERE id = ? AND (user_id = ? OR is_system_preset = 1)",
            (prompt_id, user_id),
        )

    def get_owned(self, prompt_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        return self._db.query_one(
            "SELECT * FROM system_prompts WHERE id = ? AND user_id = ?",
            (prompt_id, user_id),
        )

    def get_voice_id(self, prompt_id: str) -> Optional[str]:
        row = self._db.query_one("SELECT voice_id FROM system_prompts WHERE id = ?", (prompt_id,))
        return row.get("voice_id") if row else None

    def exists_name_for_user(
        self,
        user_id: str,
        name: str,
        *,
        exclude_id: Optional[str] = None,
    ) -> bool:
        if exclude_id:
            row = self._db.query_one(
                "SELECT id FROM system_prompts WHERE user_id = ? AND LOWER(name) = LOWER(?) AND id != ?",
                (user_id, name, exclude_id),
            )
        else:
            row = self._db.query_one(
                "SELECT id FROM system_prompts WHERE user_id = ? AND LOWER(name) = LOWER(?)",
                (user_id, name),
            )
        return row is not None

    def create(self, record: Dict[str, Any]) -> Dict[str, Any]:
        with self._db.transaction() as uow:
            if record.get("is_default"):
                uow.execute("UPDATE system_prompts SET is_default = 0 WHERE user_id = ?", (record["user_id"],))
            uow.execute(
                """
                INSERT INTO system_prompts (
                    id, user_id, name, description, content, age, gender, japanese_level,
                    personality, teaching_style, catchphrase, hobbies, avatar_url,
                    voice_id, is_default, is_system_preset, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, CURRENT_TIMESTAMP)
                """,
                (
                    record["id"],
                    record["user_id"],
                    record["name"],
                    record.get("description"),
                    record["content"],
                    record.get("age", 25),
                    record.get("gender", "female"),
                    record.get("japanese_level", "N5"),
                    record.get("personality"),
                    record.get("teaching_style"),
                    record.get("catchphrase"),
                    record.get("hobbies"),
                    record.get("avatar_url"),
                    record.get("voice_id"),
                    int(bool(record.get("is_default", False))),
                ),
            )
            created = uow.query_one("SELECT * FROM system_prompts WHERE id = ?", (record["id"],))
        return created or {}

    def update(self, prompt_id: str, user_id: str, record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        with self._db.transaction() as uow:
            if record.get("is_default"):
                uow.execute("UPDATE system_prompts SET is_default = 0 WHERE user_id = ?", (user_id,))
            uow.execute(
                """
                UPDATE system_prompts
                SET name = ?, description = ?, content = ?, age = ?, gender = ?,
                    japanese_level = ?, personality = ?, teaching_style = ?,
                    catchphrase = ?, hobbies = ?, avatar_url = ?, voice_id = ?, is_default = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND user_id = ?
                """,
                (
                    record["name"],
                    record.get("description"),
                    record["content"],
                    record.get("age", 25),
                    record.get("gender", "female"),
                    record.get("japanese_level", "N5"),
                    record.get("personality"),
                    record.get("teaching_style"),
                    record.get("catchphrase"),
                    record.get("hobbies"),
                    record.get("avatar_url"),
                    record.get("voice_id"),
                    int(bool(record.get("is_default", False))),
                    prompt_id,
                    user_id,
                ),
            )
            return uow.query_one("SELECT * FROM system_prompts WHERE id = ?", (prompt_id,))

    def delete_and_collect_attachment_paths(self, prompt_id: str, user_id: str) -> List[str]:
        with self._db.transaction() as uow:
            rows = uow.query_all(
                "SELECT storage_path, stored_path FROM attachments WHERE prompt_id = ? AND user_id = ?",
                (prompt_id, user_id),
            )
            paths = [p for r in rows if (p := r.get("storage_path") or r.get("stored_path"))]
            uow.execute("DELETE FROM attachments WHERE prompt_id = ? AND user_id = ?", (prompt_id, user_id))
            uow.execute("DELETE FROM system_prompts WHERE id = ? AND user_id = ?", (prompt_id, user_id))
        return paths
