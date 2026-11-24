"""Conversation lifecycle application service (SRP, DIP, disk cleanup on delete)."""

import uuid
from typing import Any, Callable, Dict, Optional

from src.core.attachment_storage import delete_attachment_file
from src.core.exceptions import NotFoundError, ValidationDomainError
from src.models.v1.conversation import DEFAULT_CONVERSATION_TITLE, MessageModel
from src.repositories.conversation_repo import ConversationRepository
from src.schemas.v1.conversations import CreateConversationRequest, UpdateConversationRequest


class ConversationService:
    """Manages conversation threads, Anti-IDOR access, message hydration, and cleanup."""

    def __init__(
        self,
        conv_repo: ConversationRepository,
        file_deleter: Optional[Callable[[str], bool]] = None,
    ):
        self._convs = conv_repo
        self._delete_file = file_deleter or delete_attachment_file

    def list_conversations(self, user_id: str) -> Dict[str, Any]:
        return {"conversations": self._convs.list_by_user(user_id)}

    def create_conversation(self, user_id: str, req: CreateConversationRequest) -> Dict[str, Any]:
        conv_id = str(uuid.uuid4())
        title_clean = req.title.strip() if req.title and req.title.strip() else DEFAULT_CONVERSATION_TITLE
        thread = self._convs.create(conv_id, user_id, title_clean)
        return {"conversation": thread}

    def get_messages(
        self,
        conversation_id: str,
        user_id: str,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> Dict[str, Any]:
        conv = self._convs.get_owned(conversation_id, user_id)
        if not conv:
            raise NotFoundError("Không tìm thấy cuộc trò chuyện hoặc bạn không có quyền truy cập.")

        safe_limit = max(1, min(limit, 500))
        safe_offset = max(0, offset)

        total_count = self._convs.count_messages(conversation_id)
        messages = self._convs.list_messages(conversation_id, safe_limit, safe_offset)
        raw_attachments = self._convs.list_attachments_for_messages(
            conversation_id,
            [m["id"] for m in messages],
        )
        MessageModel.enrich_messages_with_attachments(messages, raw_attachments)

        return {
            "conversation": conv,
            "messages": messages,
            "total": total_count,
            "limit": safe_limit,
            "offset": safe_offset,
        }

    def rename_conversation(
        self,
        conversation_id: str,
        user_id: str,
        req: UpdateConversationRequest,
    ) -> Dict[str, Any]:
        if not self._convs.get_owned(conversation_id, user_id):
            raise NotFoundError("Không tìm thấy cuộc trò chuyện để đổi tên.")

        title_clean = req.title.strip()
        if not title_clean:
            raise ValidationDomainError("Tiêu đề cuộc trò chuyện không được để trống.")

        updated = self._convs.rename(conversation_id, user_id, title_clean)
        return {"conversation": updated}

    def delete_conversation(self, conversation_id: str, user_id: str) -> None:
        if not self._convs.get_owned(conversation_id, user_id):
            raise NotFoundError("Không tìm thấy cuộc trò chuyện để xóa.")

        attachment_paths = self._convs.delete_and_collect_attachment_paths(conversation_id, user_id)
        for path in attachment_paths:
            self._delete_file(path)
