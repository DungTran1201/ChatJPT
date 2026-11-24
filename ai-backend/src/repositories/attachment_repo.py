"""Attachment Repository — isolates all SQL on the attachments table."""

from typing import Any, Dict, List, Optional
from src.repositories.base import BaseSQLiteRepository


class AttachmentRepository(BaseSQLiteRepository):
    """Data access layer for file attachments with strict owner scoping."""

    def create(
        self,
        *,
        user_id: str,
        file_meta: Dict[str, Any],
        conversation_id: Optional[str] = None,
        prompt_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        with self._db.transaction() as uow:
            uow.execute(
                """
                INSERT INTO attachments (
                    id, user_id, conversation_id, prompt_id,
                    filename, file_size, mime_type, category, storage_path, stored_path, checksum_sha256,
                    status, extracted_text, image_width, image_height
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    file_meta["id"],
                    user_id,
                    conversation_id,
                    prompt_id,
                    file_meta["filename"],
                    file_meta["file_size"],
                    file_meta["mime_type"],
                    file_meta["category"],
                    file_meta["storage_path"],
                    file_meta["storage_path"],
                    file_meta["checksum_sha256"],
                    file_meta["status"],
                    file_meta["extracted_text"],
                    file_meta["image_width"],
                    file_meta["image_height"],
                ),
            )
            created = uow.query_one("SELECT * FROM attachments WHERE id = ?", (file_meta["id"],))
        return created or {}

    def get_owned(
        self,
        attachment_id: str,
        user_id: str,
        *,
        include_deleted: bool = False,
    ) -> Optional[Dict[str, Any]]:
        status_clause = "" if include_deleted else " AND status != 'DELETED'"
        return self._db.query_one(
            f"SELECT * FROM attachments WHERE id = ? AND user_id = ?{status_clause}",
            (attachment_id, user_id),
        )

    def get_audio_info(self, attachment_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        return self._db.query_one(
            "SELECT id, mime_type, category FROM attachments WHERE id = ? AND user_id = ?",
            (attachment_id, user_id),
        )

    def list_filtered(
        self,
        *,
        user_id: str,
        conversation_id: Optional[str] = None,
        prompt_id: Optional[str] = None,
        status_filter: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        conditions = ["user_id = ?", "status != 'DELETED'"]
        params: List[Any] = [user_id]
        if conversation_id:
            conditions.append("conversation_id = ?")
            params.append(conversation_id)
        if prompt_id:
            conditions.append("prompt_id = ?")
            params.append(prompt_id)
        if status_filter:
            conditions.append("status = ?")
            params.append(status_filter)

        where_clause = " AND ".join(conditions)
        return self._db.query_all(
            f"SELECT * FROM attachments WHERE {where_clause} ORDER BY created_at DESC LIMIT ?",
            (*params, limit),
        )

    def list_by_prompt(self, prompt_id: str) -> List[Dict[str, Any]]:
        return self._db.query_all(
            """
            SELECT id, filename, mime_type, file_size, status, created_at
            FROM attachments
            WHERE prompt_id = ? AND status != 'DELETED'
            ORDER BY created_at DESC
            """,
            (prompt_id,),
        )

    def bind_to_message(self, attachment_id: str, message_id: str, conversation_id: str) -> None:
        self._db.execute_commit(
            """
            UPDATE attachments
            SET message_id = ?, conversation_id = ?, status = 'ATTACHED', updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (message_id, conversation_id, attachment_id),
        )

    def update_extracted_text(self, attachment_id: str, extracted_text: str) -> None:
        self._db.execute_commit(
            "UPDATE attachments SET extracted_text = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (extracted_text, attachment_id),
        )

    def delete(self, attachment_id: str, user_id: str) -> None:
        self._db.execute_commit(
            "DELETE FROM attachments WHERE id = ? AND user_id = ?",
            (attachment_id, user_id),
        )
