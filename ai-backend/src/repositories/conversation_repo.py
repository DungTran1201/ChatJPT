"""Conversation & Message Repository — isolates SQL on conversations and messages."""

from typing import Any, Dict, List, Optional
from src.repositories.base import BaseSQLiteRepository


class ConversationRepository(BaseSQLiteRepository):
    """Data access layer for conversations and their messages."""

    def list_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        return self._db.query_all(
            """
            SELECT id, user_id, title, created_at, updated_at
            FROM conversations
            WHERE user_id = ?
            ORDER BY updated_at DESC
            """,
            (user_id,),
        )

    def get_owned(self, conversation_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        return self._db.query_one(
            """
            SELECT id, user_id, title, created_at, updated_at
            FROM conversations
            WHERE id = ? AND user_id = ?
            """,
            (conversation_id, user_id),
        )

    def create(self, conversation_id: str, user_id: str, title: str) -> Dict[str, Any]:
        with self._db.transaction() as uow:
            uow.execute(
                "INSERT INTO conversations (id, user_id, title) VALUES (?, ?, ?)",
                (conversation_id, user_id, title),
            )
            created = uow.query_one("SELECT * FROM conversations WHERE id = ?", (conversation_id,))
        return created or {}

    def rename(self, conversation_id: str, user_id: str, title: str) -> Optional[Dict[str, Any]]:
        with self._db.transaction() as uow:
            uow.execute(
                """
                UPDATE conversations
                SET title = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND user_id = ?
                """,
                (title, conversation_id, user_id),
            )
            return uow.query_one("SELECT * FROM conversations WHERE id = ?", (conversation_id,))

    def touch(self, conversation_id: str) -> None:
        self._db.execute_commit(
            "UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (conversation_id,),
        )

    def delete_and_collect_attachment_paths(self, conversation_id: str, user_id: str) -> List[str]:
        """Deletes owned conversation atomically and returns disk paths of linked attachments."""
        with self._db.transaction() as uow:
            rows = uow.query_all(
                "SELECT storage_path, stored_path FROM attachments WHERE conversation_id = ?",
                (conversation_id,),
            )
            paths = [
                p
                for r in rows
                if (p := r.get("storage_path") or r.get("stored_path"))
            ]
            uow.execute(
                "DELETE FROM attachments WHERE conversation_id = ?",
                (conversation_id,),
            )
            uow.execute(
                "DELETE FROM conversations WHERE id = ? AND user_id = ?",
                (conversation_id, user_id),
            )
        return paths

    def count_messages(self, conversation_id: str) -> int:
        row = self._db.query_one(
            "SELECT COUNT(*) AS total FROM messages WHERE conversation_id = ?",
            (conversation_id,),
        )
        return int(row["total"]) if row else 0

    def list_messages(self, conversation_id: str, limit: int, offset: int) -> List[Dict[str, Any]]:
        return self._db.query_all(
            """
            SELECT id, conversation_id, role, content, model_used, tokens_prompt, tokens_completion,
                   source, status, created_at, updated_at, sensei_id, voice_id,
                   audio_attachment_id, audio_duration_ms, stt_language, stt_confidence
            FROM messages
            WHERE conversation_id = ?
            ORDER BY created_at ASC, id ASC
            LIMIT ? OFFSET ?
            """,
            (conversation_id, limit, offset),
        )

    def list_attachments_for_messages(
        self,
        conversation_id: str,
        message_ids: List[str],
    ) -> List[Dict[str, Any]]:
        if not message_ids:
            return []
        placeholders = ", ".join("?" for _ in message_ids)
        return self._db.query_all(
            f"""
            SELECT id, message_id, filename, mime_type, file_size, status, created_at
            FROM attachments
            WHERE conversation_id = ? AND status != 'DELETED' AND message_id IN ({placeholders})
            """,
            (conversation_id, *message_ids),
        )

    def get_recent_context(self, conversation_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        rows = self._db.query_all(
            """
            SELECT role, content FROM messages
            WHERE conversation_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (conversation_id, limit),
        )
        rows.reverse()
        return rows

    def insert_user_message(
        self,
        *,
        message_id: str,
        conversation_id: str,
        content: str,
        audio_attachment_id: Optional[str] = None,
        audio_duration_ms: int = 0,
        stt_language: str = "auto",
    ) -> None:
        self._db.execute_commit(
            """
            INSERT INTO messages (
                id, conversation_id, role, content, model_used,
                audio_attachment_id, audio_duration_ms, stt_language
            ) VALUES (?, ?, 'user', ?, 'client', ?, ?, ?)
            """,
            (message_id, conversation_id, content, audio_attachment_id, audio_duration_ms, stt_language),
        )

    def insert_assistant_message(
        self,
        *,
        message_id: str,
        conversation_id: str,
        content: str,
        model_used: str,
        sensei_id: Optional[str] = None,
        voice_id: Optional[str] = None,
    ) -> None:
        self._db.execute_commit(
            """
            INSERT INTO messages (id, conversation_id, role, content, model_used, sensei_id, voice_id)
            VALUES (?, ?, 'assistant', ?, ?, ?, ?)
            """,
            (message_id, conversation_id, content, model_used, sensei_id, voice_id),
        )
