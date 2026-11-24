"""User Repository — isolates all SQL operations on the users table."""

from typing import Any, Dict, List, Optional, Tuple
from src.repositories.base import BaseSQLiteRepository

_USER_PUBLIC_COLUMNS = """
    id, email, full_name, username, avatar_url, bio, phone_number,
    age, occupation, interests, japanese_level, learning_goal,
    custom_bg_url, bg_opacity, bg_blur, bg_dim, accent_color, ui_font_size,
    discord_id, discord_username,
    theme_preference, language_preference,
    response_show_translation, response_show_furigana,
    response_highlight_grammar, response_show_romaji,
    response_grammar_breakdown, response_audio_speech,
    response_bilingual_mode,
    status, created_at, last_login_at, password_changed_at
"""

_USER_PREFERENCES_COLUMNS = """
    theme_preference, language_preference, custom_bg_url,
    bg_opacity, bg_blur, bg_dim, accent_color, ui_font_size,
    response_show_translation, response_show_furigana,
    response_highlight_grammar, response_show_romaji,
    response_grammar_breakdown, response_audio_speech,
    response_bilingual_mode
"""


class UserRepository(BaseSQLiteRepository):
    """Data access layer for users and user-scoped summary counts."""

    def get_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        return self._db.query_one(
            f"SELECT {_USER_PUBLIC_COLUMNS} FROM users WHERE id = ?",
            (user_id,),
        )

    def get_by_email_with_password(self, email: str) -> Optional[Dict[str, Any]]:
        return self._db.query_one(
            f"SELECT {_USER_PUBLIC_COLUMNS}, hashed_password FROM users WHERE email = ? COLLATE NOCASE",
            (email,),
        )

    def get_auth_credentials(self, user_id: str) -> Optional[Dict[str, Any]]:
        return self._db.query_one(
            "SELECT id, email, hashed_password FROM users WHERE id = ?",
            (user_id,),
        )

    def exists_by_email(self, email: str, *, exclude_user_id: Optional[str] = None) -> bool:
        if exclude_user_id:
            row = self._db.query_one(
                "SELECT id FROM users WHERE email = ? COLLATE NOCASE AND id != ?",
                (email, exclude_user_id),
            )
        else:
            row = self._db.query_one(
                "SELECT id FROM users WHERE email = ? COLLATE NOCASE",
                (email,),
            )
        return row is not None

    def exists_by_username(self, username: str, *, exclude_user_id: str) -> bool:
        row = self._db.query_one(
            "SELECT id FROM users WHERE username = ? COLLATE NOCASE AND id != ?",
            (username, exclude_user_id),
        )
        return row is not None

    def create(self, user_id: str, email: str, full_name: str, hashed_password: str) -> Dict[str, Any]:
        with self._db.transaction() as uow:
            uow.execute(
                """
                INSERT INTO users (id, email, full_name, hashed_password, status)
                VALUES (?, ?, ?, ?, 'ACTIVE')
                """,
                (user_id, email, full_name, hashed_password),
            )
            created = uow.query_one(
                "SELECT id, email, full_name, status, created_at FROM users WHERE id = ?",
                (user_id,),
            )
        return created or {}

    def touch_last_login(self, user_id: str) -> None:
        self._db.execute_commit(
            "UPDATE users SET last_login_at = CURRENT_TIMESTAMP WHERE id = ?",
            (user_id,),
        )

    def update_fields(self, user_id: str, assignments: List[str], params: List[Any]) -> None:
        if not assignments:
            return
        sql = f"UPDATE users SET {', '.join(assignments)} WHERE id = ?"
        self._db.execute_commit(sql, (*params, user_id))

    def update_avatar(self, user_id: str, avatar_url: str) -> None:
        self._db.execute_commit(
            "UPDATE users SET avatar_url = ? WHERE id = ?",
            (avatar_url, user_id),
        )

    def update_email(self, user_id: str, new_email: str) -> None:
        self._db.execute_commit(
            "UPDATE users SET email = ? WHERE id = ?",
            (new_email, user_id),
        )

    def update_password(self, user_id: str, new_hashed_password: str) -> None:
        self._db.execute_commit(
            """
            UPDATE users
            SET hashed_password = ?, password_changed_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (new_hashed_password, user_id),
        )

    def get_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        return self._db.query_one(
            f"SELECT {_USER_PREFERENCES_COLUMNS} FROM users WHERE id = ?",
            (user_id,),
        )

    def get_usage_stats(self, user_id: str) -> Tuple[int, int]:
        conv_stat = self._db.query_one(
            "SELECT COUNT(*) AS total FROM conversations WHERE user_id = ?",
            (user_id,),
        )
        msg_stat = self._db.query_one(
            """
            SELECT COUNT(*) AS total
            FROM messages m
            JOIN conversations c ON m.conversation_id = c.id
            WHERE c.user_id = ?
            """,
            (user_id,),
        )
        return (
            int(conv_stat["total"]) if conv_stat else 0,
            int(msg_stat["total"]) if msg_stat else 0,
        )
